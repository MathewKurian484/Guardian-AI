from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import sys
import json
import tempfile
import shutil
import git

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class RepoQATool:
    
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
            temperature=0.1,
            google_api_key=api_key
        )
        
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.documents = []
        self.repo_path = None
    
    def index_repository(self, repo_path: Path) -> Dict[str, Any]:
        self.repo_path = repo_path
        
        extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.cs',
            '.md', '.txt', '.rst', '.html', '.css',
            '.json', '.yaml', '.yml', '.toml', '.xml'
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
                'status': 'error',
                'message': 'No documents found to index',
                'documents_count': 0
            }
        
        print(f"✓ Loaded {len(self.documents)} documents")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        print("Splitting documents into chunks...")
        splits = text_splitter.split_documents(self.documents)
        print(f"✓ Created {len(splits)} chunks")
        
        print("Creating vector store (this may take a moment)...")
        self.vectorstore = FAISS.from_documents(splits, self.embeddings)
        
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
        template = """Answer the question based only on the following context:

{context}

Question: {question}

Provide a detailed answer with specific examples from the code. If you reference code, include the file name."""

        prompt = ChatPromptTemplate.from_template(template)
        
        self.qa_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print(f"✓ Indexed {len(self.documents)} documents ({len(splits)} chunks)\n")
        
        return {
            'status': 'success',
            'documents_count': len(self.documents),
            'chunks_count': len(splits)
        }
    
    def _should_index_file(self, file_path: Path) -> bool:
        ignore_dirs = {'node_modules', 'venv', 'env', '.git', '__pycache__', 
                      'build', 'dist', '.idea', '.vscode', 'target', 'bin', 'obj'}
        
        parts = file_path.parts
        if any(ignored_dir in parts for ignored_dir in ignore_dirs):
            return False
        
        return True
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        if not self.qa_chain:
            return {
                'status': 'error',
                'error': 'Repository not indexed. Please index a repository first.'
            }
        
        try:
            answer = self.qa_chain.invoke(question)
            
            docs = self.retriever.invoke(question)
            sources = [doc.metadata.get('source', 'unknown') for doc in docs]
            
            return {
                'status': 'success',
                'question': question,
                'answer': answer,
                'sources': list(set(sources[:5])),  # Top 5 unique sources
                'source_count': len(docs)
            }
        except Exception as e:
            return {
                'status': 'error',
                'question': question,
                'error': str(e)
            }
    
    def ask_questions_interactive(self):
        if not self.qa_chain:
            print("Error: Repository not indexed.")
            return
        
        print("\n" + "="*70)
        print("INTERACTIVE Q&A MODE")
        print("="*70)
        print("Ask questions about the repository. Type 'exit' or 'quit' to stop.\n")
        
        while True:
            try:
                question = input("Question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\nExiting Q&A mode...")
                    break
                
                result = self.ask_question(question)
                
                if result['status'] == 'success':
                    print(f"\nAnswer: {result['answer']}\n")
                    if result['sources']:
                        print(f"Sources: {', '.join(result['sources'][:3])}\n")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error')}\n")
                    
            except KeyboardInterrupt:
                print("\n\nExiting Q&A mode...")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
    
    @staticmethod
    def _handle_remove_readonly(func, path, exc):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)


if __name__ == "__main__":
    import argparse
    
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found!")
        print("\nPlease set your Gemini API key:")
        print("  Windows PowerShell: $env:GOOGLE_API_KEY='your-key-here'")
        print("  Linux/Mac: export GOOGLE_API_KEY='your-key-here'")
        print("  Or create a .env file with: GOOGLE_API_KEY=your-key-here")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='Repository Q&A Tool - Ask questions about any GitHub repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive Q&A
  python qa_tool.py https://github.com/user/repo --interactive
  
  # Ask a single question
  python qa_tool.py https://github.com/user/repo --question "What does this project do?"
  
  # Ask multiple questions
  python qa_tool.py https://github.com/user/repo -q "What's the main purpose?" -q "How do I install it?"
  
  # Use a different model
  python qa_tool.py https://github.com/user/repo --interactive --model gemini-1.5-pro
  
  # Save answers to JSON
  python qa_tool.py https://github.com/user/repo -q "Summarize this project" --output summary.json
        """
    )
    
    parser.add_argument(
        'repo_url',
        help='GitHub repository URL'
    )
    
    parser.add_argument(
        '--question', '-q',
        action='append',
        help='Question to ask (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive Q&A session'
    )
    
    parser.add_argument(
        '--model',
        default='gemini-2.5-pro-preview-03-25',
        help='Gemini model to use (default: gemini-2.5-pro-preview-03-25)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file path for answers'
    )
    
    args = parser.parse_args()
    
    if not args.question and not args.interactive:
        print("Error: Please provide either --question or --interactive")
        parser.print_help()
        sys.exit(1)
    
    print("="*70)
    print("REPOSITORY Q&A TOOL")
    print("="*70)
    print(f"\nRepository: {args.repo_url}")
    print(f"Model: {args.model}\n")
    print("="*70)
    
    qa_tool = RepoQATool(model_name=args.model)
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix='guardian_qa_')
        print(f"Cloning repository to {temp_dir}...")
        
        git.Repo.clone_from(args.repo_url, temp_dir)
        print(f"✓ Repository cloned successfully\n")
        
        repo_path = Path(temp_dir)
        index_result = qa_tool.index_repository(repo_path)
        
        if index_result['status'] == 'error':
            print(f"Error: {index_result['message']}")
            sys.exit(1)
        
        if args.interactive:
            qa_tool.ask_questions_interactive()
        
        elif args.question:
            results = []
            
            for question in args.question:
                print(f"\nQ: {question}")
                result = qa_tool.ask_question(question)
                
                if result['status'] == 'success':
                    print(f"A: {result['answer']}\n")
                    if result['sources']:
                        print(f"Sources: {', '.join(result['sources'][:3])}")
                    print()
                    results.append(result)
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}\n")
                    results.append(result)
            
            if args.output:
                output_data = {
                    'repository': args.repo_url,
                    'model': args.model,
                    'total_questions': len(args.question),
                    'results': results
                }
                
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"✓ Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            print(f"\nCleaning up temporary directory...")
            try:
                shutil.rmtree(temp_dir, onerror=qa_tool._handle_remove_readonly)
                print("✓ Cleanup complete")
            except Exception as e:
                print(f"Warning: Cleanup failed: {e}")
    
    print("\n" + "="*70)
    print("Q&A SESSION COMPLETE!")
    print("="*70)
