import os
import json
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import git
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class CodeAuditorAgent:
    RELEVANT_EXTENSIONS = {'.py', '.js', '.java', '.html', '.css', '.jsx', '.tsx', '.ts', '.cpp', '.c', '.h', '.go', '.rb', '.php', '.swift', '.kt'}
    IGNORE_EXTENSIONS = {'.jpg', '.png', '.gif', '.pdf', '.zip', '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite', '.ico', '.svg', '.woff', '.ttf', '.eot'}
    IGNORE_DIRS = {'node_modules', 'venv', 'env', '.git', '__pycache__', 'build', 'dist', '.idea', '.vscode', 'target', 'bin', 'obj'}
    
    def __init__(self, model_name: str = "gemini-2.5-flash", chunk_size: int = 30):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise ValueError(
                "GOOGLE_API_KEY not found. Please set it as an environment variable."
            )
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1,
            convert_system_message_to_human=True,
            google_api_key=api_key
        )
        self.chunk_size = chunk_size
        self.violations = []
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        parts = file_path.parts
        if any(ignored_dir in parts for ignored_dir in self.IGNORE_DIRS):
            return False

        suffix = file_path.suffix.lower()
        if suffix in self.IGNORE_EXTENSIONS:
            return False
        
        if suffix in self.RELEVANT_EXTENSIONS:
            return True
        
        return False
    
    def _get_language_from_extension(self, extension: str) -> str:
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.html': 'html',
            '.css': 'css',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        return lang_map.get(extension, 'text')
    
    def _split_into_chunks(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        lines = content.split('\n')
        chunks = []
        
        for i in range(0, len(lines), self.chunk_size):
            chunk_lines = lines[i:i + self.chunk_size]
            chunk_text = '\n'.join(chunk_lines)
            
            chunks.append({
                'content': chunk_text,
                'file_path': file_path,
                'start_line': i + 1,
                'end_line': min(i + self.chunk_size, len(lines)),
                'total_lines': len(lines)
            })
        
        return chunks
    
    def _analyze_chunk(self, chunk: Dict[str, Any], technical_brief: str, language: str) -> List[Dict[str, Any]]:
        prompt = f"""You are an expert code auditor. Your task is to determine if the following code snippet violates any of the rules in the provided technical brief.
                    **TECHNICAL BRIEF:**
                    {technical_brief}
                    **CODE SNIPPET (File: {chunk['file_path']}, Lines {chunk['start_line']}-{chunk['end_line']}):**
                    ```{language}
                    {chunk['content']}
                    ```
                    ---
                    Analyze the code snippet against the brief. If you find one or more violations, respond with a JSON list. Each item in the list should be a dictionary with the keys: "violating_code", "explanation", and "rule_violated". 
                    If there are no violations in this snippet, respond with an empty list: []
                    Your response must be ONLY the JSON list, nothing else.
                    """
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            violations = json.loads(response_text)

            if violations and isinstance(violations, list):
                for violation in violations:
                    violation['file'] = chunk['file_path']
                    violation['line'] = chunk['start_line']
                    # Keep old keys for compatibility
                    violation['file_path'] = chunk['file_path']
                    violation['line_number'] = chunk['start_line']
                
                return violations
            
            return []
        
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse LLM response as JSON for {chunk['file_path']} lines {chunk['start_line']}-{chunk['end_line']}: {e}")
            print(f"Response was: {response_text[:200]}")
            return []
        
        except Exception as e:
            print(f"Error analyzing chunk {chunk['file_path']} lines {chunk['start_line']}-{chunk['end_line']}: {e}")
            return []
    
    def _analyze_file(self, file_path: Path, repo_root: Path, technical_brief: str) -> int:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = file_path.relative_to(repo_root)
            
            language = self._get_language_from_extension(file_path.suffix)
            
            chunks = self._split_into_chunks(content, str(relative_path))
            
            violations_found = 0
            for chunk in chunks:
                chunk_violations = self._analyze_chunk(chunk, technical_brief, language)
                if chunk_violations:
                    self.violations.extend(chunk_violations)
                    violations_found += len(chunk_violations)
            
            return violations_found
        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return 0
    
    def scan_repository(self, repo_url: str, technical_brief: str) -> Dict[str, Any]:
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp(prefix='guardian_audit_')
            print(f"Cloning repository to {temp_dir}...")
            
            repo = git.Repo.clone_from(repo_url, temp_dir)
            print(f"✓ Repository cloned successfully")
            
            self.violations = []
            
            repo_path = Path(temp_dir)
            total_files = 0
            analyzed_files = 0
            
            print("\nScanning files...")
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    
                    if self._should_analyze_file(file_path):
                        analyzed_files += 1
                        print(f"Analyzing: {file_path.relative_to(repo_path)}")
                        
                        violations_in_file = self._analyze_file(
                            file_path, 
                            repo_path, 
                            technical_brief
                        )
                        
                        if violations_in_file > 0:
                            print(f"  ⚠ Found {violations_in_file} violation(s)")
            
            result = {
                'status': 'success',
                'repository': repo_url,
                'total_files': total_files,
                'analyzed_files': analyzed_files,
                'total_violations': len(self.violations),
                'violations': self.violations
            }
            
            print(f"\n✓ Scan complete:")
            print(f"  - Total files: {total_files}")
            print(f"  - Analyzed files: {analyzed_files}")
            print(f"  - Violations found: {len(self.violations)}")
            
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'repository': repo_url,
                'error': str(e),
                'violations': []
            }
        
        finally:
            if temp_dir and os.path.exists(temp_dir):
                print(f"\nCleaning up temporary directory...")
                try:
                    shutil.rmtree(temp_dir, onerror=self._handle_remove_readonly)
                    print("✓ Cleanup complete")
                except Exception as e:
                    print(f"Warning: Cleanup failed: {e}")
    
    @staticmethod
    def _handle_remove_readonly(func, path, exc):
        """Handle removal of read-only files on Windows."""
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)


# Contract-compliant function (as specified in PROGRESS.md)
def code_auditor_agent(repo_url: str, technical_brief: str) -> str:
    auditor = CodeAuditorAgent()
    result = auditor.scan_repository(repo_url, technical_brief)
    
    return json.dumps(result['violations'], indent=2)


class ComplianceChecker:
    
    def __init__(self, model_name: str = "gemini-2.5-pro-preview-03-25"):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found. Please set it as an environment variable.")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=api_key
        )
        
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.documents = []
    
    def index_repository(self, repo_path: Path) -> Dict[str, Any]:
        extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.cs',
            '.md', '.txt', '.rst',
            '.json', '.yaml', '.yml', '.toml'
        ]
        
        print("Loading documents from repository...")
        self.documents = []
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                if self._should_index_file(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        doc = Document(
                            page_content=content,
                            metadata={
                                'source': str(file_path.relative_to(repo_path)),
                                'file_name': file_path.name,
                                'extension': file_path.suffix
                            }
                        )
                        self.documents.append(doc)
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
        
        if not self.documents:
            return {
                'status': 'warning',
                'message': 'No documents found to index',
                'documents_count': 0
            }
        
        print(f"Loaded {len(self.documents)} documents")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        print("Splitting documents into chunks...")
        splits = text_splitter.split_documents(self.documents)
        print(f"Created {len(splits)} chunks")
        
        print("Creating vector store (this may take a moment)...")
        self.vectorstore = FAISS.from_documents(splits, self.embeddings)
        
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
        template = """Answer the question based only on the following context:

{context}

Question: {question}

Provide a detailed answer with specific examples from the code."""

        prompt = ChatPromptTemplate.from_template(template)
        
        self.qa_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return {
            'status': 'success',
            'documents_count': len(self.documents),
            'chunks_count': len(splits)
        }
    
    def _should_index_file(self, file_path: Path) -> bool:
        ignore_dirs = {'node_modules', 'venv', 'env', '.git', '__pycache__', 
                      'build', 'dist', '.idea', '.vscode', 'target'}
        
        parts = file_path.parts
        if any(ignored_dir in parts for ignored_dir in ignore_dirs):
            return False
        
        return True
    
    def check_compliance(
        self,
        repo_url: str,
        guidelines: List[str]
    ) -> Dict[str, Any]:
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp(prefix='guardian_compliance_')
            print(f"Cloning repository to {temp_dir}...")
            
            git.Repo.clone_from(repo_url, temp_dir)
            print(f"✓ Repository cloned successfully\n")
            
            repo_path = Path(temp_dir)
            index_result = self.index_repository(repo_path)
            
            if index_result['status'] == 'warning':
                return {
                    'status': 'error',
                    'error': 'No documents found to index',
                    'compliance_checks': []
                }
            
            print(f"✓ Indexed {index_result['documents_count']} documents "
                  f"({index_result['chunks_count']} chunks)\n")
            
            compliance_results = []
            
            print("Running compliance checks...")
            for i, guideline in enumerate(guidelines, 1):
                print(f"  [{i}/{len(guidelines)}] Checking: {guideline[:60]}...")
                
                question = f"Does this repository comply with the following requirement: {guideline}? Please provide specific evidence from the code or documentation."
                
                try:
                    docs = self.retriever.invoke(guideline)
                    
                    answer = self.qa_chain.invoke(guideline)
                    
                    evidence_details = []
                    for doc in docs[:3]:
                        source_file = doc.metadata.get('source', 'unknown')
                        content = doc.page_content.strip()
                        
                        code_snippet = content[:150] + "..." if len(content) > 150 else content
                        
                        line_number = self._estimate_line_number(repo_path, source_file, content)
                        
                        evidence_details.append({
                            'file': source_file,
                            'line': line_number,
                            'code_snippet': code_snippet
                        })
                    
                    compliance_results.append({
                        'guideline': guideline,
                        'assessment': answer,
                        'evidence_sources': [doc.metadata.get('source', 'unknown') for doc in docs[:3]],
                        'evidence_details': evidence_details  # New: detailed evidence with line numbers
                    })
                except Exception as e:
                    compliance_results.append({
                        'guideline': guideline,
                        'assessment': f'Error checking compliance: {str(e)}',
                        'evidence_sources': [],
                        'evidence_details': []
                    })
            
            return {
                'status': 'success',
                'repository': repo_url,
                'compliance_checks': compliance_results,
                'total_guidelines_checked': len(guidelines)
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'repository': repo_url,
                'error': str(e),
                'compliance_checks': []
            }
        
        finally:
            if temp_dir and os.path.exists(temp_dir):
                print(f"\nCleaning up temporary directory...")
                try:
                    shutil.rmtree(temp_dir, onerror=self._handle_remove_readonly)
                    print("✓ Cleanup complete")
                except Exception as e:
                    print(f"Warning: Cleanup failed: {e}")
    
    @staticmethod
    def _handle_remove_readonly(func, path, exc):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    def _estimate_line_number(self, repo_path: Path, source_file: str, chunk_content: str) -> int:
        try:
            file_path = repo_path / source_file
            if not file_path.exists():
                return 1
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_lines = f.readlines()
            
            chunk_lines = chunk_content.split('\n')
            search_line = None
            for line in chunk_lines:
                stripped = line.strip()
                if stripped and len(stripped) > 10:  # Must be meaningful
                    search_line = stripped
                    break
            
            if not search_line:
                return 1
            
            for i, file_line in enumerate(file_lines, 1):
                if search_line in file_line.strip():
                    return i
            
            return 1
            
        except Exception as e:
            return 1


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your Gemini API key before running.")
        print("\nOptions:")
        print("1. Set in PowerShell: $env:GOOGLE_API_KEY='your-key-here'")
        print("2. Create .env file with: GOOGLE_API_KEY=your-key-here")
        exit(1)
    
    parser = argparse.ArgumentParser(
        description='Guardian AI - Independent Code Analysis & Compliance Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  audit       Line-by-line code auditing (exhaustive scanning)
  compliance  RAG-based compliance checking (semantic search)

Examples:
  # AUDIT MODE - Find specific violations
  python code_tool.py audit https://github.com/user/repo
  python code_tool.py audit https://github.com/user/repo --brief "All functions need docstrings"
  python code_tool.py audit https://github.com/user/repo --brief-file rules.txt --output report.json

  # COMPLIANCE MODE - Check against guidelines
  python code_tool.py compliance https://github.com/user/repo
  python code_tool.py compliance https://github.com/user/repo --guideline "Must have LICENSE file"
  python code_tool.py compliance https://github.com/user/repo --guidelines-file guidelines.txt
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    audit_parser = subparsers.add_parser('audit', help='Line-by-line code audit')
    audit_parser.add_argument(
        'repo_url',
        nargs='?',
        help='GitHub repository URL to audit'
    )
    audit_parser.add_argument(
        '--brief', '-b',
        action='append',
        help='Technical brief rule (can be specified multiple times)'
    )
    audit_parser.add_argument(
        '--brief-file',
        help='File containing technical brief (one rule per line)'
    )
    audit_parser.add_argument(
        '--model',
        default='gemini-2.5-flash',
        help='Gemini model to use (default: gemini-2.5-flash)'
    )
    audit_parser.add_argument(
        '--chunk-size',
        type=int,
        default=30,
        help='Number of lines per chunk (default: 30, range: 20-40)'
    )
    audit_parser.add_argument(
        '--max-display',
        type=int,
        default=10,
        help='Maximum violations to display (default: 10)'
    )
    audit_parser.add_argument(
        '--output', '-o',
        help='Output JSON file path'
    )
    audit_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed statistics'
    )
    
    compliance_parser = subparsers.add_parser('compliance', help='RAG-based compliance checking')
    compliance_parser.add_argument(
        'repo_url',
        nargs='?',
        help='GitHub repository URL to check'
    )
    compliance_parser.add_argument(
        '--guideline', '-g',
        action='append',
        help='Compliance guideline (can be specified multiple times)'
    )
    compliance_parser.add_argument(
        '--guidelines-file',
        help='File containing guidelines (one per line)'
    )
    compliance_parser.add_argument(
        '--model',
        default='gemini-2.5-pro-preview-03-25',
        help='Gemini model to use (default: gemini-2.5-pro-preview-03-25)'
    )
    compliance_parser.add_argument(
        '--max-display',
        type=int,
        default=5,
        help='Maximum compliance checks to display (default: 5)'
    )
    compliance_parser.add_argument(
        '--output', '-o',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        print("\n" + "="*70)
        print("Please specify a mode: 'audit' or 'compliance'")
        print("="*70)
        sys.exit(1)
    
    if args.mode == 'audit':
        if not args.repo_url:
            print("No repository URL provided. Using example repository...\n")
            repo_url = "https://github.com/kolipakulaHARSHA/FINANCE_MANAGEMENT_APP"
        else:
            repo_url = args.repo_url
        
        if args.brief_file:
            try:
                with open(args.brief_file, 'r') as f:
                    technical_brief = f.read()
            except FileNotFoundError:
                print(f"Error: Brief file not found: {args.brief_file}")
                sys.exit(1)
        elif args.brief:
            technical_brief = '\n'.join(args.brief)
        else:
            technical_brief = """
        Code Quality Requirements:
        1. All image elements must have valid alt attributes
        2. User data must be encrypted during transmission
        3. Password fields must implement minimum strength requirements
        4. CSRF tokens must be present in all forms
        5. API endpoints must implement rate limiting
        """
        
        print("="*70)
        print("CODE AUDITOR AGENT - Line-by-Line Analysis")
        print("="*70)
        print(f"\nRepository: {repo_url}")
        print(f"Model: {args.model}")
        print(f"Chunk Size: {args.chunk_size} lines")
        print(f"\nTechnical Brief:")
        print(technical_brief)
        print("\n" + "="*70)
        
        if args.detailed:
            auditor = CodeAuditorAgent(
                model_name=args.model,
                chunk_size=args.chunk_size
            )
            result = auditor.scan_repository(repo_url, technical_brief)
            violations = result['violations']
            
            print(f"\n\n=== AUDIT RESULTS ===")
            print(f"Total files scanned: {result['total_files']}")
            print(f"Files analyzed: {result['analyzed_files']}")
            print(f"Violations found: {result['total_violations']}")
            print("="*70)
        else:
            result_json = code_auditor_agent(repo_url, technical_brief)
            violations = json.loads(result_json)
            
            print(f"\n\n=== AUDIT RESULTS ===")
            print(f"Violations found: {len(violations)}")
            print("="*70)
        
        if violations:
            print(f"\nViolations Found:")
            display_count = min(len(violations), args.max_display)
            
            violations_display = []
            for violation in violations[:display_count]:
                violations_display.append({
                    "file": violation.get('file', violation.get('file_path', 'N/A')),
                    "line": violation.get('line', violation.get('line_number', 'N/A')),
                    "violating_code": violation.get('violating_code', 'N/A'),
                    "explanation": violation.get('explanation', 'N/A'),
                    "rule_violated": violation.get('rule_violated', 'N/A')
                })
            
            print(json.dumps(violations_display, indent=2))
            
            if len(violations) > args.max_display:
                print(f"\n... and {len(violations) - args.max_display} more violations")
                print(f"    (use --max-display {len(violations)} to see all)")
        else:
            print("\nViolations Found: []")
            print("\n✓ No violations found!")
        
        if args.output:
            formatted_violations = []
            for violation in violations:
                formatted_violations.append({
                    "file": violation.get('file', violation.get('file_path', 'N/A')),
                    "line": violation.get('line', violation.get('line_number', 'N/A')),
                    "violating_code": violation.get('violating_code', 'N/A'),
                    "explanation": violation.get('explanation', 'N/A'),
                    "rule_violated": violation.get('rule_violated', 'N/A')
                })
            
            output_data = {
                'repository': repo_url,
                'technical_brief': technical_brief,
                'model': args.model,
                'chunk_size': args.chunk_size,
                'violations': formatted_violations,
                'total_violations': len(violations)
            }
            
            if args.detailed and 'result' in locals():
                output_data['stats'] = {
                    'total_files': result['total_files'],
                    'analyzed_files': result['analyzed_files']
                }
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n✓ Results saved to: {args.output}")
    
    elif args.mode == 'compliance':
        if not args.repo_url:
            print("No repository URL provided. Using example repository...\n")
            repo_url = "https://github.com/kolipakulaHARSHA/FINANCE_MANAGEMENT_APP"
        else:
            repo_url = args.repo_url
        
        if args.guidelines_file:
            try:
                with open(args.guidelines_file, 'r') as f:
                    guidelines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except FileNotFoundError:
                print(f"Error: Guidelines file not found: {args.guidelines_file}")
                sys.exit(1)
        elif args.guideline:
            guidelines = args.guideline
        else:
            guidelines = [
                "The project must have a LICENSE file",
                "The project must have a README with installation instructions",
                "The project must have proper documentation",
                "The code should follow security best practices",
                "The project should have a clear contribution guide"
            ]
        
        print("="*70)
        print("COMPLIANCE CHECKER - RAG-Based Analysis")
        print("="*70)
        print(f"\nRepository: {repo_url}")
        print(f"Model: {args.model}")
        print(f"\nGuidelines to check ({len(guidelines)}):")
        for i, g in enumerate(guidelines, 1):
            print(f"  {i}. {g}")
        print("\n" + "="*70)
        
        checker = ComplianceChecker(model_name=args.model)
        result = checker.check_compliance(repo_url, guidelines)
        
        if result['status'] == 'error':
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        print(f"\n\n=== COMPLIANCE RESULTS ===")
        print(f"Guidelines checked: {result['total_guidelines_checked']}")
        print("="*70)
        
        compliance_checks = result['compliance_checks']
        
        violations = []
        for check in compliance_checks:
            assessment_lower = check['assessment'].lower()
            is_violation = any(keyword in assessment_lower for keyword in [
                'no', 'not', 'does not', 'missing', 'absent', 'lacking', 
                'cannot find', 'no information', 'no evidence', 'not found'
            ])
            
            if is_violation:
                evidence_details = check.get('evidence_details', [])
                
                if evidence_details:
                    first_evidence = evidence_details[0]
                    file_name = first_evidence.get('file', 'Repository-wide')
                    line_number = first_evidence.get('line', 1)
                    code_snippet = first_evidence.get('code_snippet', 'N/A - Compliance issue')
                else:
                    file_name = check['evidence_sources'][0] if check['evidence_sources'] else 'Repository-wide'
                    line_number = 1
                    code_snippet = 'N/A - Compliance issue'
                
                violations.append({
                    "file": file_name,
                    "line": line_number,
                    "violating_code": code_snippet,
                    "explanation": check['assessment'],
                    "rule_violated": check['guideline']
                })
        
        if violations:
            print(f"\nViolations Found:")
            display_count = min(len(violations), args.max_display)
            print(json.dumps(violations[:display_count], indent=2))
            
            if len(violations) > args.max_display:
                print(f"\n... and {len(violations) - args.max_display} more violations")
                print(f"    (use --max-display {len(violations)} to see all)")
        else:
            print("\nViolations Found: []")
            print("\n✓ All compliance checks passed!")
        
        if args.output:
            output_data = {
                'repository': repo_url,
                'guidelines': guidelines,
                'model': args.model,
                'violations': violations,  # Use new violation format
                'total_violations': len(violations),
                'total_guidelines_checked': result['total_guidelines_checked'],
                'compliance_checks': compliance_checks
            }
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n✓ Results saved to: {args.output}")
    
    print("\n" + "="*70)
    print(f"{args.mode.upper()} complete!")
    print("="*70)
