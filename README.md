# Guardian AI

AI-powered compliance and code analysis platform that helps developers ensure their code follows regulatory requirements.

![Guardian AI](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![React](https://img.shields.io/badge/react-18.2-61DAFB.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## Features

- **Code Auditing** - Scan GitHub repositories for compliance violations against regulatory documents
- **Legal Document Analysis** - Extract compliance requirements from PDF regulatory documents using RAG
- **Repository Q&A** - Ask natural language questions about any codebase
- **Real-time Scanning** - Live progress updates during code analysis
- **Dark/Light Mode** - Modern UI with theme support

## Architecture

```
GuardianAI/
├── Backend/                    # FastAPI Python backend
│   ├── api.py                  # Main API endpoints
│   ├── guardian_agent.py       # AI agent orchestration
│   ├── Github_scanner/         # Code scanning tools
│   │   ├── code_tool.py        # Repository auditing
│   │   └── qa_tool.py          # Q&A functionality
│   ├── Guardian-Legal-analyzer-main/
│   │   └── legal_tool.py       # PDF analysis with RAG
│   └── Main_Orchestrator/      # Workflow orchestration
│
└── Frontend/                   # React TypeScript frontend
    └── src/
        ├── pages/              # Dashboard, CodeAudit, QAChat
        ├── components/         # Reusable UI components
        └── services/           # API client
```

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **LangChain** - LLM orchestration and RAG pipelines
- **Google Gemini** - AI models (gemini-2.5-flash, gemini-2.5-pro)
- **ChromaDB / FAISS** - Vector stores for semantic search
- **GitPython** - Repository cloning and analysis

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tool
- **Framer Motion** - Animations
- **React Router** - Navigation

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API Key

### Backend Setup

1. Navigate to the Backend directory:
   ```bash
   cd Backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your-google-api-key-here
   ```

5. Start the API server:
   ```bash
   python api.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the Frontend directory:
   ```bash
   cd Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   
   The app will be available at `http://localhost:5173`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/api/audit/code` | POST | Audit a GitHub repository |
| `/api/audit/code/stream` | GET | Audit with SSE progress updates |
| `/api/qa/init` | POST | Initialize Q&A session for a repo |
| `/api/qa/ask` | POST | Ask a question about indexed repo |
| `/api/analyze/legal` | POST | Analyze a legal/regulatory PDF |
| `/api/upload/pdf` | POST | Upload a PDF file |
| `/api/agent/query` | POST | Natural language query to agent |

## Usage

### Code Audit

1. Go to the **Code Audit** page
2. Enter a GitHub repository URL
3. Either upload a compliance PDF or enter requirements manually
4. Click **Run Audit** to scan for violations

### Repository Q&A

1. Go to the **Q&A Chat** page
2. Enter a GitHub repository URL
3. Click **Index Repository** to process the codebase
4. Ask questions about the code in natural language

### Legal Document Analysis

Upload regulatory PDFs to automatically extract compliance requirements that can be used for code auditing.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `DEFAULT_MODEL` | No | Default LLM model |
| `DEFAULT_TEMPERATURE` | No | Model temperature (0-1) |

## Project Structure

```
Backend/
├── api.py                 # FastAPI application & endpoints
├── guardian_agent.py      # LangGraph agent with tools
├── requirements.txt       # Python dependencies
├── Github_scanner/
│   ├── code_tool.py       # CodeAuditorAgent class
│   ├── qa_tool.py         # RepoQATool class
│   └── requirements.txt   # Scanner-specific deps
├── Guardian-Legal-analyzer-main/
│   └── legal_tool.py      # RAG-based PDF analysis
└── Main_Orchestrator/
    ├── main.py            # Orchestration logic
    └── contracts.py       # Function contracts

Frontend/
├── src/
│   ├── App.tsx            # Main app with routing
│   ├── pages/
│   │   ├── Dashboard.tsx  # Home page
│   │   ├── CodeAudit.tsx  # Audit interface
│   │   └── QAChat.tsx     # Q&A interface
│   ├── components/
│   │   ├── Navbar.tsx     # Navigation
│   │   ├── FormattedMessage.tsx
│   │   └── ViolationResults.tsx
│   ├── services/
│   │   └── api.ts         # API client
│   └── contexts/
│       ├── ThemeContext.tsx
│       └── AppStateContext.tsx
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [LangChain](https://langchain.com/) for LLM orchestration
- [Google Gemini](https://ai.google.dev/) for AI models
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
