import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

GUARDIAN_ROOT = Path(__file__).parent
sys.path.insert(0, str(GUARDIAN_ROOT / 'Guardian-Legal-analyzer-main'))
sys.path.insert(0, str(GUARDIAN_ROOT / 'Github_scanner'))

from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

if not os.environ.get('GOOGLE_API_KEY'):
    raise ValueError("GOOGLE_API_KEY not found. Please set it in .env file")


def legal_analyzer_wrapper(input_str: str) -> str:
    try:
        from legal_tool import legal_analyst_tool
        
        if '|' in input_str:
            pdf_path, question = input_str.split('|', 1)
        else:
            pdf_path = input_str
            question = (
                "Create a concise, bullet-pointed technical brief for a developer. "
                "List the key compliance requirements from this document that can "
                "be checked in a codebase."
            )
        
        pdf_path = pdf_path.strip()
        question = question.strip()
        
        if not os.path.isabs(pdf_path):
            possible_paths = [
                Path(pdf_path),
                GUARDIAN_ROOT / pdf_path,
                GUARDIAN_ROOT / 'GuardianAI-Orchestrator' / pdf_path,
            ]
            for p in possible_paths:
                if p.exists():
                    pdf_path = str(p)
                    break
        
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at '{pdf_path}'"
        
        result = legal_analyst_tool(
            pdf_file_path=pdf_path,
            question=question,
            use_existing_db=True,
            filter_by_current_pdf=True
        )
        
        return result
        
    except Exception as e:
        return f"Error in legal analysis: {str(e)}"


def code_auditor_wrapper(input_str: str) -> str:
    try:
        from code_tool import CodeAuditorAgent
        
        if '|' not in input_str:
            return "Error: Input must be in format 'repo_url|technical_brief'"
        
        repo_url, technical_brief = input_str.split('|', 1)
        repo_url = repo_url.strip()
        technical_brief = technical_brief.strip()
        
        auditor = CodeAuditorAgent(model_name="gemini-2.5-flash")
        result = auditor.scan_repository(repo_url, technical_brief)
        
        if result['status'] == 'error':
            return f"Error: {result.get('error', 'Unknown error')}"
        
        violations = result.get('violations', [])
        
        summary = f"Code Audit Results:\n"
        summary += f"- Repository: {repo_url}\n"
        summary += f"- Files scanned: {result.get('total_files', 0)}\n"
        summary += f"- Files analyzed: {result.get('analyzed_files', 0)}\n"
        summary += f"- Violations found: {len(violations)}\n\n"
        
        if violations:
            summary += "Violations:\n"
            for i, v in enumerate(violations[:10], 1):  # Show first 10
                summary += f"{i}. {v.get('file', 'Unknown')} (line {v.get('line', '?')})\n"
                summary += f"   Issue: {v.get('explanation', 'No explanation')}\n"
                summary += f"   Rule: {v.get('rule_violated', 'Unknown rule')}\n"
            
            if len(violations) > 10:
                summary += f"\n... and {len(violations) - 10} more violations\n"
        else:
            summary += "✓ No violations found!\n"
        
        global _last_audit_result
        _last_audit_result = result
        
        return summary
        
    except Exception as e:
        return f"Error in code audit: {str(e)}"


def qa_tool_wrapper(input_str: str) -> str:
    try:
        from qa_tool import RepoQATool
        
        if '|' not in input_str:
            return "Error: Input must be in format 'repo_url|question'"
        
        repo_url, question = input_str.split('|', 1)
        repo_url = repo_url.strip()
        question = question.strip()
        
        qa_tool = RepoQATool(model_name="gemini-2.5-pro-preview-03-25")
        answer = qa_tool.ask_question(repo_url, question)
        
        return answer
        
    except Exception as e:
        return f"Error in Q&A: {str(e)}"


_last_audit_result = None


def create_guardian_agent(model_name: str = "gemini-2.5-pro-preview-03-25", verbose: bool = True):
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        google_api_key=os.environ['GOOGLE_API_KEY']
    )
    
    tools = [
        Tool(
            name="Legal_Analyzer",
            func=legal_analyzer_wrapper,
            description="""
            Analyzes regulatory PDF documents to extract compliance requirements.
            
            WHEN TO USE:
            - User asks about regulations, laws, or compliance documents
            - You need to understand what rules a codebase should follow
            - User wants a technical brief from a PDF
            
            INPUT FORMAT: "pdf_path|question" or just "pdf_path"
            Examples:
            - "sample_regulation.pdf"
            - "gdpr.pdf|What are the data protection requirements?"
            
            OUTPUT: Plain-English technical brief listing compliance requirements
            
            IMPORTANT: Use this FIRST when analyzing code compliance, before using Code_Auditor.
            """
        ),
        
        Tool(
            name="Code_Auditor",
            func=code_auditor_wrapper,
            description="""
            Scans code repositories for violations against compliance requirements.
            
            WHEN TO USE:
            - User wants to audit/scan/check code for violations
            - You have compliance requirements and need to check code
            - User asks if code follows certain rules
            
            INPUT FORMAT: "repo_url|technical_brief"
            Example: "https://github.com/user/repo|Check for: data encryption, input validation, security headers"
            
            OUTPUT: Summary of violations found with file locations and explanations
            
            IMPORTANT: 
            - You need a technical brief (from Legal_Analyzer or user) before using this
            - The technical_brief should be specific compliance requirements
            """
        ),
        
        Tool(
            name="QA_Tool",
            func=qa_tool_wrapper,
            description="""
            Answers questions about a code repository by analyzing its contents.
            
            WHEN TO USE:
            - User asks "what does this code do?"
            - Need to understand code architecture before making recommendations
            - User wants to know how something is implemented
            - Need context about the codebase
            
            INPUT FORMAT: "repo_url|question"
            Example: "https://github.com/user/repo|How is authentication implemented?"
            
            OUTPUT: Detailed answer based on actual code with source citations
            
            TIPS:
            - Use this to understand code before suggesting fixes
            - Good for explaining violations in more detail
            - Can answer multiple questions about same repo
            """
        )
    ]
    
    system_message = """You are Guardian AI, an expert compliance and code analysis assistant. You help users ensure their code follows regulatory requirements.

Your capabilities:
1. Analyze regulatory documents (PDFs) to extract compliance requirements
2. Audit code repositories to find violations
3. Answer detailed questions about codebases

IMPORTANT WORKFLOW:
- If user asks to check compliance: FIRST use Legal_Analyzer to get requirements, THEN use Code_Auditor
- If user asks about code: Use QA_Tool
- If user asks for recommendations: Audit first, then use QA_Tool to understand code, then provide advice

Always think step by step and explain your reasoning."""
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )
    
    return agent


class GuardianAgent:
    
    def __init__(self, model_name: str = "gemini-2.5-pro-preview-03-25", verbose: bool = True):
        self.model_name = model_name
        self.verbose = verbose
        self.agent = create_guardian_agent(model_name, verbose)
    
    def run(self, query: str) -> Dict[str, Any]:
        messages = [HumanMessage(content=query)]
        result = self.agent.invoke({"messages": messages})
        
        output_message = result['messages'][-1].content if result['messages'] else ""
        
        return {
            'output': output_message,
            'intermediate_steps': result.get('intermediate_steps', []),
            'messages': result.get('messages', [])
        }
    
    def ask(self, query: str) -> str:
        result = self.run(query)
        return result['output']


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Guardian AI - Intelligent Compliance & Code Analysis Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Check compliance (agent will use Legal_Analyzer then Code_Auditor)
  python guardian_agent.py "Check if https://github.com/user/repo complies with sample_regulation.pdf"

  # Analyze regulation only
  python guardian_agent.py "What are the key requirements in gdpr.pdf?"

  # Ask about code
  python guardian_agent.py "What does the project at https://github.com/user/repo do?"

  # Complex query (agent will use multiple tools)
  python guardian_agent.py "Audit https://github.com/user/repo against gdpr.pdf and explain how to fix violations"

  # Interactive mode
  python guardian_agent.py --interactive

The agent will automatically decide which tools to use and in what order!
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Your question or request in natural language'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive chat session'
    )
    
    parser.add_argument(
        '--model',
        default='gemini-2.5-pro-preview-03-25',
        help='Gemini model to use (default: gemini-2.5-pro-preview-03-25)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Hide agent thinking process (only show final answer)'
    )
    
    parser.add_argument(
        '--save',
        help='Save full results to JSON file'
    )
    
    args = parser.parse_args()
    
    print("🤖 Initializing Guardian AI Agent...")
    agent = GuardianAgent(model_name=args.model, verbose=not args.quiet)
    print("✅ Agent ready!\n")
    
    if args.interactive:
        print("="*70)
        print("GUARDIAN AI - INTERACTIVE MODE")
        print("="*70)
        print("\nYou can ask me anything about:")
        print("  • Regulatory compliance requirements")
        print("  • Code auditing and violation detection")
        print("  • Understanding what code does")
        print("  • Recommendations for fixing issues")
        print("\nType 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                query = input("\n🧑 You: ").strip()
                
                if query.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Goodbye!")
                    break
                
                if not query:
                    continue
                
                print("\n🤖 Guardian AI:")
                result = agent.run(query)
                print(f"\n{result['output']}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    elif args.query:
        print("="*70)
        print(f"QUERY: {args.query}")
        print("="*70)
        print()
        
        result = agent.run(args.query)
        
        print("\n" + "="*70)
        print("FINAL ANSWER")
        print("="*70)
        print(f"\n{result['output']}\n")
        
        if args.save:
            output = {
                'query': args.query,
                'answer': result['output'],
                'model': args.model,
                'intermediate_steps': [
                    {
                        'action': step[0].tool,
                        'action_input': step[0].tool_input,
                        'observation': step[1]
                    }
                    for step in result.get('intermediate_steps', [])
                ]
            }
            
            global _last_audit_result
            if _last_audit_result:
                output['full_audit_results'] = _last_audit_result
            
            with open(args.save, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"✅ Full results saved to: {args.save}\n")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
