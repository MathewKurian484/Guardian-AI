import axios, { AxiosInstance } from 'axios';
import type {
  CodeAuditRequest,
  CodeAuditResponse,
  QARequest,
  QAResponse,
  QAInitResponse,
  LegalAnalysisRequest,
  LegalAnalysisResponse,
  FileUploadResponse,
  HealthCheckResponse,
  AgentQueryRequest,
  AgentQueryResponse,
} from '@/types';

class GuardianAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 86400000, // 24 hours for long-running operations
    });
  }

  // Health check
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/health');
    return response.data;
  }

  // Code Audit
  async auditCode(request: CodeAuditRequest): Promise<CodeAuditResponse> {
    const response = await this.client.post<CodeAuditResponse>(
      '/api/audit/code',
      request
    );
    return response.data;
  }

  // Q&A - Initialize session
  async initQASession(request: QARequest): Promise<QAInitResponse> {
    const response = await this.client.post<QAInitResponse>(
      '/api/qa/init',
      request
    );
    return response.data;
  }

  // Q&A - Ask question
  async askQuestion(
    sessionId: string,
    request: QARequest
  ): Promise<QAResponse> {
    const response = await this.client.post<QAResponse>(
      `/api/qa/ask?session_id=${sessionId}`,
      request
    );
    return response.data;
  }

  // Q&A - Get chat history
  async getChatHistory(sessionId: string): Promise<{
    session_id: string;
    messages: Array<{ role: string; content: string; timestamp: string }>;
    repo_url: string;
  }> {
    const response = await this.client.get(`/api/qa/history/${sessionId}`);
    return response.data;
  }

  // Q&A - Delete session
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`/api/qa/session/${sessionId}`);
    return response.data;
  }

  // Legal Analysis
  async analyzeLegal(
    request: LegalAnalysisRequest
  ): Promise<LegalAnalysisResponse> {
    const response = await this.client.post<LegalAnalysisResponse>(
      '/api/analyze/legal',
      request
    );
    return response.data;
  }

  // Upload PDF
  async uploadPDF(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<FileUploadResponse>(
      '/api/upload/pdf',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  // Agent Query (Natural Language)
  async agentQuery(request: AgentQueryRequest): Promise<AgentQueryResponse> {
    const response = await this.client.post<AgentQueryResponse>(
      '/api/agent/query',
      request
    );
    return response.data;
  }
}

// Export singleton instance
export const api = new GuardianAPI();

// Export class for testing
export default GuardianAPI;
