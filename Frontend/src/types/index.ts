// API Request/Response Types

export interface CodeAuditRequest {
  repo_url: string;
  pdf_path?: string;
  technical_brief?: string;
  model_name?: string;
}

export interface QARequest {
  repo_url: string;
  question: string;
  model_name?: string;
}

export interface LegalAnalysisRequest {
  pdf_path: string;
  question?: string;
}

export interface AgentQueryRequest {
  query: string;
  model_name?: string;
}

export interface Violation {
  violating_code: string;
  explanation: string;
  rule_violated: string;
  file: string;
  line: number;
  file_path: string;
  line_number: number;
}

export interface AuditDetails {
  mode: string;
  repository: string;
  total_violations: number;
  violations: Violation[];
  files_scanned?: number;
  scan_statistics?: Record<string, any>;
}

export interface ToolResults {
  legal_brief?: string;
  audit_results?: string;
  audit_details?: AuditDetails;
}

export interface Plan {
  tools_needed: string[];
  execution_order: string[];
  reasoning: string;
  pdf_path?: string;
  repo_url?: string;
  audit_mode?: string;
}

export interface CodeAuditResponse {
  timestamp: string;
  query: string;
  model: string;
  plan: Plan;
  tool_results: ToolResults;
  final_answer?: string;
  metadata: {
    guardian_version: string;
    mode: string;
  };
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface QAResponse {
  session_id: string;
  question: string;
  answer: string;
  timestamp: string;
  messages: ChatMessage[];
}

export interface QAInitResponse {
  session_id: string;
  repo_url: string;
  status: string;
  message: string;
}

export interface LegalAnalysisResponse {
  pdf_path: string;
  question: string;
  analysis: string;
  timestamp: string;
}

export interface FileUploadResponse {
  filename: string;
  path: string;
  size: number;
  message: string;
}

export interface HealthCheckResponse {
  status: string;
  api_key_configured: boolean;
  active_sessions: number;
  timestamp: string;
}

export interface IntermediateStep {
  action: string;
  action_input: string;
  observation: string;
}

export interface AgentQueryResponse {
  query: string;
  answer: string;
  intermediate_steps: IntermediateStep[];
  timestamp: string;
  model: string;
}

// UI State Types
export interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  details?: string;
}

export type AnalysisMode = 'audit' | 'qa' | 'agent';

export interface SessionState {
  sessionId?: string;
  repoUrl?: string;
  messages: ChatMessage[];
}
