import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from queue import Queue

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
from sse_starlette.sse import EventSourceResponse
import uvicorn

GUARDIAN_ROOT = Path(__file__).parent
sys.path.insert(0, str(GUARDIAN_ROOT / 'Guardian-Legal-analyzer-main'))
sys.path.insert(0, str(GUARDIAN_ROOT / 'Github_scanner'))

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get('GOOGLE_API_KEY'):
    raise ValueError("GOOGLE_API_KEY not found. Please set it in .env file")

from guardian_agent import GuardianAgent
from code_tool import CodeAuditorAgent
from qa_tool import RepoQATool
from legal_tool import legal_analyst_tool

app = FastAPI(
    title="Guardian AI API",
    description="AI-powered compliance and code analysis platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeAuditRequest(BaseModel):
    repo_url: str
    pdf_path: Optional[str] = None
    technical_brief: Optional[str] = None
    model_name: Optional[str] = "gemini-2.5-flash"

class QARequest(BaseModel):
    repo_url: str
    question: str
    model_name: Optional[str] = "gemini-2.5-pro"

class LegalAnalysisRequest(BaseModel):
    pdf_path: str
    question: Optional[str] = None

class AgentQueryRequest(BaseModel):
    query: str
    model_name: Optional[str] = "gemini-2.5-pro"

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_or_create_qa_session(session_id: str, repo_url: str, model_name: str) -> RepoQATool:
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "qa_tool": RepoQATool(model_name=model_name),
            "repo_url": repo_url,
            "indexed": False,
            "messages": []
        }
    return chat_sessions[session_id]

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Guardian AI API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.environ.get('GOOGLE_API_KEY')),
        "active_sessions": len(chat_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/audit/code")
async def audit_code(request: CodeAuditRequest):
    try:
        technical_brief = request.technical_brief
        legal_brief = None
        
        if request.pdf_path:
            pdf_full_path = Path(request.pdf_path)
            if not pdf_full_path.is_absolute():
                possible_paths = [
                    GUARDIAN_ROOT / request.pdf_path,
                    GUARDIAN_ROOT / 'GuardianAI-Orchestrator' / request.pdf_path,
                ]
                for p in possible_paths:
                    if p.exists():
                        pdf_full_path = p
                        break
            
            if not pdf_full_path.exists():
                raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_path}")
            
            legal_brief = legal_analyst_tool(
                pdf_file_path=str(pdf_full_path),
                question="Create a concise, bullet-pointed technical brief for a developer. List the key compliance requirements from this document that can be checked in a codebase.",
                use_existing_db=True,
                filter_by_current_pdf=True
            )
            technical_brief = legal_brief
        
        if not technical_brief:
            raise HTTPException(status_code=400, detail="Either pdf_path or technical_brief must be provided")
        
        auditor = CodeAuditorAgent(model_name=request.model_name)
        result = auditor.scan_repository(request.repo_url, technical_brief)
        
        response = {
            "timestamp": datetime.now().isoformat(),
            "query": f"Audit {request.repo_url}",
            "model": request.model_name,
            "plan": {
                "tools_needed": ["Legal_Analyzer", "Code_Auditor"] if request.pdf_path else ["Code_Auditor"],
                "execution_order": ["Legal_Analyzer", "Code_Auditor"] if request.pdf_path else ["Code_Auditor"],
                "reasoning": "Analyzing code for compliance violations",
                "pdf_path": request.pdf_path,
                "repo_url": request.repo_url,
                "audit_mode": "audit"
            },
            "tool_results": {
                "legal_brief": legal_brief,
                "audit_details": result
            },
            "metadata": {
                "guardian_version": "1.0",
                "mode": "code_audit"
            }
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit/code/stream")
async def audit_code_stream(
    repo_url: str,
    pdf_path: Optional[str] = None,
    model_name: str = "gemini-2.5-flash"
):
    async def event_generator():
        try:
            technical_brief = None
            legal_brief = None
            
            if pdf_path:
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "analyzing_pdf",
                        "message": "Analyzing compliance document..."
                    })
                }
                
                pdf_full_path = Path(pdf_path)
                if not pdf_full_path.is_absolute():
                    possible_paths = [
                        GUARDIAN_ROOT / pdf_path,
                        GUARDIAN_ROOT / 'GuardianAI-Orchestrator' / pdf_path,
                    ]
                    for p in possible_paths:
                        if p.exists():
                            pdf_full_path = p
                            break
                
                if not pdf_full_path.exists():
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": f"PDF file not found: {pdf_path}"})
                    }
                    return
                
                legal_brief = legal_analyst_tool(
                    pdf_file_path=str(pdf_full_path),
                    question="Create a concise, bullet-pointed technical brief for a developer.",
                    use_existing_db=True,
                    filter_by_current_pdf=True
                )
                technical_brief = legal_brief
                
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "pdf_analyzed",
                        "message": "✓ Compliance rules extracted"
                    })
                }
            
            if not technical_brief:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Either pdf_path or technical_brief must be provided"})
                }
                return
            
            auditor = CodeAuditorAgent(model_name=model_name)
            
            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": "cloning",
                    "message": "Cloning repository..."
                })
            }
            
            result = await asyncio.to_thread(
                scan_repository_with_progress,
                auditor,
                repo_url,
                technical_brief,
                event_generator_callback=lambda msg: None
            )
            
            import tempfile
            import shutil
            import git
            
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp(prefix='guardian_audit_')
                
                repo = await asyncio.to_thread(git.Repo.clone_from, repo_url, temp_dir)
                
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "cloned",
                        "message": "✓ Repository cloned"
                    })
                }
                
                repo_path = Path(temp_dir)
                total_files = sum(1 for _ in repo_path.rglob('*') if _.is_file())
                
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "scanning",
                        "message": f"Scanning {total_files} files...",
                        "total_files": total_files
                    })
                }
                
                analyzed_files = 0
                auditor.violations = []
                
                for file_path in repo_path.rglob('*'):
                    if file_path.is_file() and auditor._should_analyze_file(file_path):
                        analyzed_files += 1
                        relative_path = str(file_path.relative_to(repo_path))
                        
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "status": "analyzing",
                                "message": f"Analyzing: {relative_path}",
                                "current_file": relative_path,
                                "analyzed_files": analyzed_files
                            })
                        }
                        
                        violations_count = await asyncio.to_thread(
                            auditor._analyze_file,
                            file_path,
                            repo_path,
                            technical_brief
                        )
                        
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "status": "file_complete",
                                "file": relative_path,
                                "violations": violations_count,
                                "analyzed_files": analyzed_files
                            })
                        }
                

                result = {
                    'status': 'success',
                    'repository': repo_url,
                    'total_files': total_files,
                    'analyzed_files': analyzed_files,
                    'total_violations': len(auditor.violations),
                    'violations': auditor.violations
                }
                
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "timestamp": datetime.now().isoformat(),
                        "query": f"Audit {repo_url}",
                        "model": model_name,
                        "tool_results": {
                            "legal_brief": legal_brief,
                            "audit_details": result
                        }
                    })
                }
                
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    await asyncio.to_thread(shutil.rmtree, temp_dir, onerror=lambda f, p, e: None)
                    
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())

def scan_repository_with_progress(auditor, repo_url, technical_brief, event_generator_callback):
    return auditor.scan_repository(repo_url, technical_brief)

@app.post("/api/qa/init")
async def initialize_qa_session(request: QARequest):
    import tempfile
    import shutil
    import git
    
    try:
        session_id = f"session_{datetime.now().timestamp()}"
        
        session = get_or_create_qa_session(session_id, request.repo_url, request.model_name)
        qa_tool = session["qa_tool"]
        
        temp_dir = tempfile.mkdtemp(prefix="guardian_qa_")
        
        try:
            git.Repo.clone_from(request.repo_url, temp_dir)
            
            repo_path = Path(temp_dir)
            index_result = qa_tool.index_repository(repo_path)
            
            if index_result['status'] == 'error':
                raise Exception(index_result.get('message', 'Failed to index repository'))
            
            session["indexed"] = True
            session["temp_dir"] = temp_dir
            
            return {
                "session_id": session_id,
                "repo_url": request.repo_url,
                "status": "ready",
                "message": "Repository indexed successfully",
                "indexed_files": index_result.get('file_count', 0),
                "indexed_chunks": index_result.get('chunk_count', 0)
            }
            
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/ask")
async def ask_question(session_id: str, request: QARequest):
    try:
        if session_id not in chat_sessions:
            raise HTTPException(
                status_code=404, 
                detail=f"Session {session_id} not found. Please initialize a session first using /api/qa/init"
            )
        
        session = chat_sessions[session_id]
        qa_tool = session["qa_tool"]
        
        if not session.get("indexed", False):
            raise HTTPException(
                status_code=400,
                detail="Repository not indexed. Please initialize the session first."
            )
        
        result = qa_tool.ask_question(request.question)
        
        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        answer = result.get('answer', '')
        sources = result.get('sources', [])
        
        timestamp = datetime.now().isoformat()
        session["messages"].append({
            "role": "user",
            "content": request.question,
            "timestamp": timestamp
        })
        session["messages"].append({
            "role": "assistant",
            "content": answer,
            "timestamp": timestamp
        })
        
        return {
            "session_id": session_id,
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "timestamp": timestamp,
            "messages": session["messages"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/history/{session_id}")
async def get_chat_history(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": chat_sessions[session_id]["messages"],
        "repo_url": chat_sessions[session_id]["repo_url"]
    }

@app.post("/api/analyze/legal")
async def analyze_legal_document(request: LegalAnalysisRequest):
    try:
        pdf_full_path = Path(request.pdf_path)
        if not pdf_full_path.is_absolute():
            possible_paths = [
                GUARDIAN_ROOT / request.pdf_path,
                GUARDIAN_ROOT / 'GuardianAI-Orchestrator' / request.pdf_path,
            ]
            for p in possible_paths:
                if p.exists():
                    pdf_full_path = p
                    break
        
        if not pdf_full_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_path}")
        
        question = request.question or "Create a concise, bullet-pointed technical brief for a developer. List the key compliance requirements from this document that can be checked in a codebase."
        
        result = legal_analyst_tool(
            pdf_file_path=str(pdf_full_path),
            question=question,
            use_existing_db=True,
            filter_by_current_pdf=True
        )
        
        return {
            "pdf_path": request.pdf_path,
            "question": question,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        upload_dir = GUARDIAN_ROOT / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "filename": file.filename,
            "path": str(file_path.relative_to(GUARDIAN_ROOT)),
            "size": len(content),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/query")
async def agent_query(request: AgentQueryRequest):
    try:
        agent = GuardianAgent(model_name=request.model_name, verbose=False)
        
        result = agent.run(request.query)
        
        return {
            "query": request.query,
            "answer": result.get("output", ""),
            "intermediate_steps": [
                {
                    "action": step[0].tool,
                    "action_input": step[0].tool_input,
                    "observation": step[1]
                }
                for step in result.get("intermediate_steps", [])
            ],
            "timestamp": datetime.now().isoformat(),
            "model": request.model_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/qa/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": "Session deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    print("🚀 Starting Guardian AI API Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )