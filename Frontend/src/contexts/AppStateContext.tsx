import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CodeAuditResponse, ChatMessage } from '@/types';

interface ProgressUpdate {
  status: string;
  message: string;
  current_file?: string;
  analyzed_files?: number;
  total_files?: number;
  violations?: any[];
}

interface CodeAuditState {
  repoUrl: string;
  pdfFile: File | null;
  pdfFileName: string;
  modelName: string;
  results: CodeAuditResponse | null;
  isLoading: boolean;
  progressUpdates: ProgressUpdate[];
  currentProgress: ProgressUpdate | null;
}

interface QAChatState {
  repoUrl: string;
  pdfFile: File | null;
  pdfFileName: string;
  modelName: string;
  messages: ChatMessage[];
  sessionId: string | null;
  isInitialized: boolean;
  isLoading: boolean;
}

interface AppState {
  codeAudit: CodeAuditState;
  qaChat: QAChatState;
}

interface AppStateContextType {
  state: AppState;
  updateCodeAudit: (updates: Partial<CodeAuditState>) => void;
  updateQAChat: (updates: Partial<QAChatState>) => void;
  resetCodeAudit: () => void;
  resetQAChat: () => void;
}

const defaultCodeAuditState: CodeAuditState = {
  repoUrl: '',
  pdfFile: null,
  pdfFileName: '',
  modelName: 'gemini-2.0-flash-exp',
  results: null,
  isLoading: false,
  progressUpdates: [],
  currentProgress: null,
};

const defaultQAChatState: QAChatState = {
  repoUrl: '',
  pdfFile: null,
  pdfFileName: '',
  modelName: 'gemini-2.0-flash-exp',
  messages: [],
  sessionId: null,
  isInitialized: false,
  isLoading: false,
};

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

const STORAGE_KEY = 'guardian-ai-state';

export const AppStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(() => {
    // Load from localStorage on mount
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          codeAudit: { ...defaultCodeAuditState, ...parsed.codeAudit, pdfFile: null }, // Don't restore file object
          qaChat: { ...defaultQAChatState, ...parsed.qaChat, pdfFile: null },
        };
      }
    } catch (error) {
      console.error('Error loading saved state:', error);
    }
    return {
      codeAudit: defaultCodeAuditState,
      qaChat: defaultQAChatState,
    };
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    try {
      const toSave = {
        codeAudit: {
          ...state.codeAudit,
          pdfFile: null, // Don't save file objects
          isLoading: false, // Reset loading states
          progressUpdates: [], // Clear progress on reload
          currentProgress: null,
        },
        qaChat: {
          ...state.qaChat,
          pdfFile: null,
          isLoading: false,
        },
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch (error) {
      console.error('Error saving state:', error);
    }
  }, [state]);

  const updateCodeAudit = (updates: Partial<CodeAuditState>) => {
    setState((prev) => ({
      ...prev,
      codeAudit: { ...prev.codeAudit, ...updates },
    }));
  };

  const updateQAChat = (updates: Partial<QAChatState>) => {
    setState((prev) => ({
      ...prev,
      qaChat: { ...prev.qaChat, ...updates },
    }));
  };

  const resetCodeAudit = () => {
    setState((prev) => ({
      ...prev,
      codeAudit: defaultCodeAuditState,
    }));
  };

  const resetQAChat = () => {
    setState((prev) => ({
      ...prev,
      qaChat: defaultQAChatState,
    }));
  };

  return (
    <AppStateContext.Provider
      value={{
        state,
        updateCodeAudit,
        updateQAChat,
        resetCodeAudit,
        resetQAChat,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
};

export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider');
  }
  return context;
};
