import { useState } from 'react';
import { motion } from 'framer-motion';
import { Github, Send, Loader2, MessageSquare, AlertCircle, RotateCcw } from 'lucide-react';
import { api } from '@/services/api';
import FormattedMessage from '@/components/FormattedMessage';
import { useAppState } from '@/contexts/AppStateContext';
import type { ChatMessage, ErrorState } from '@/types';

const QAChat = () => {
  const { state, updateQAChat, resetQAChat } = useAppState();
  const { repoUrl, messages, sessionId, isInitialized, isLoading } = state.qaChat;
  
  const [question, setQuestion] = useState('');
  const [error, setError] = useState<ErrorState>({ hasError: false });

  const initializeSession = async () => {
    if (!repoUrl) {
      setError({ hasError: true, message: 'Please enter a repository URL' });
      return;
    }

    try {
      updateQAChat({ isLoading: true });
      setError({ hasError: false });

      const response = await api.initQASession({
        repo_url: repoUrl,
        question: 'Initialize',
      });

      updateQAChat({
        sessionId: response.session_id,
        isInitialized: true,
        isLoading: false,
      });
    } catch (err) {
      setError({
        hasError: true,
        message: 'Failed to initialize session',
        details: err instanceof Error ? err.message : 'Unknown error',
      });
      updateQAChat({ isLoading: false });
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) return;

    if (!sessionId) {
      await initializeSession();
      return;
    }

    try {
      updateQAChat({ isLoading: true });
      setError({ hasError: false });

      const userMessage: ChatMessage = {
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };

      updateQAChat({
        messages: [...messages, userMessage],
      });
      setQuestion('');

      const response = await api.askQuestion(sessionId, {
        repo_url: repoUrl,
        question: question,
      });

      updateQAChat({
        messages: [...messages, userMessage, {
          role: 'assistant',
          content: response.answer,
          timestamp: response.timestamp,
        }],
        isLoading: false,
      });
    } catch (err) {
      setError({
        hasError: true,
        message: 'Failed to get answer',
        details: err instanceof Error ? err.message : 'Unknown error',
      });
      updateQAChat({ isLoading: false });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-4 gradient-text">
            Repository Q&A Assistant
          </h1>
          <p className="text-gray-600 dark:text-slate-400">
            Ask questions about any GitHub repository and get instant answers
          </p>
        </motion.div>

        {/* Repository Input */}
        {!isInitialized && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card mb-8"
          >
            <label className="block text-sm font-semibold mb-2 text-gray-700 dark:text-slate-300">
              <Github className="inline w-4 h-4 mr-2" />
              GitHub Repository URL
            </label>
            <div className="flex gap-4">
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => updateQAChat({ repoUrl: e.target.value })}
                placeholder="https://github.com/username/repository"
                className="input-field flex-1"
              />
              <button
                onClick={initializeSession}
                disabled={isLoading}
                className="btn-primary whitespace-nowrap flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Indexing...
                  </>
                ) : (
                  <>
                    <MessageSquare className="w-5 h-5" />
                    Start Chat
                  </>
                )}
              </button>
            </div>

            {error.hasError && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-red-700 dark:text-red-400">
                    {error.message}
                  </div>
                  {error.details && (
                    <div className="text-sm text-red-600 dark:text-red-500 mt-1">
                      {error.details}
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Chat Interface */}
        {isInitialized && (
          <div className="space-y-6">
            {/* Repository Info */}
            <div className="glass-panel p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <Github className="w-4 h-4 text-gray-600 dark:text-slate-400" />
                <span className="text-gray-600 dark:text-slate-400">
                  {repoUrl}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => updateQAChat({ isInitialized: false, sessionId: null })}
                  className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                >
                  Change Repository
                </button>
                <button
                  onClick={() => {
                    resetQAChat();
                    setQuestion('');
                    setError({ hasError: false });
                  }}
                  className="btn-outline text-sm flex items-center gap-2 px-4 py-2"
                  title="Clear all chat history and reset"
                >
                  <RotateCcw className="w-4 h-4" />
                  Clear All
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="glass-panel p-6 min-h-[400px] max-h-[600px] overflow-y-auto space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-slate-500">
                  <MessageSquare className="w-16 h-16 mb-4" />
                  <p className="text-lg">Ask a question to get started</p>
                </div>
              ) : (
                messages.map((message: ChatMessage, index: number) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`chat-message ${
                      message.role === 'user' ? 'chat-user' : 'chat-assistant'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                          message.role === 'user'
                            ? 'bg-primary-500'
                            : 'bg-gradient-to-br from-accent-500 to-primary-500'
                        }`}
                      >
                        <span className="text-white text-sm font-semibold">
                          {message.role === 'user' ? 'U' : 'AI'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <FormattedMessage 
                          content={message.content} 
                          role={message.role}
                        />
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
              {isLoading && (
                <div className="chat-message chat-assistant">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
                    <span className="text-gray-500 dark:text-slate-400">
                      AI is thinking...
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="glass-panel p-4">
              <div className="flex gap-4">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about the repository..."
                  className="input-field flex-1"
                  disabled={isLoading}
                />
                <button
                  onClick={handleAskQuestion}
                  disabled={isLoading || !question.trim()}
                  className="btn-primary whitespace-nowrap flex items-center gap-2 disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                  Send
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QAChat;
