import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Github, AlertCircle, CheckCircle2, Loader2, RotateCcw } from 'lucide-react';
import { api } from '@/services/api';
import type { ErrorState } from '@/types';
import ViolationResults from '@/components/ViolationResults';
import { useAppState } from '@/contexts/AppStateContext';

interface ProgressUpdate {
  status: string;
  message: string;
  current_file?: string;
  analyzed_files?: number;
  total_files?: number;
  violations?: any;
  file?: string;
}

const CodeAudit = () => {
  const { state, updateCodeAudit, resetCodeAudit } = useAppState();
  const { repoUrl, pdfFile, pdfFileName, modelName, results, isLoading, progressUpdates, currentProgress } = state.codeAudit;
  
  const [pdfPath, setPdfPath] = useState('');
  const [error, setError] = useState<ErrorState>({ hasError: false });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      updateCodeAudit({ pdfFile: file, pdfFileName: file.name });
      try {
        updateCodeAudit({ isLoading: true });
        const uploadResult = await api.uploadPDF(file);
        setPdfPath(uploadResult.path);
        updateCodeAudit({ isLoading: false });
      } catch (err) {
        setError({
          hasError: true,
          message: 'Failed to upload PDF',
          details: err instanceof Error ? err.message : 'Unknown error',
        });
        updateCodeAudit({ isLoading: false });
      }
    }
  };

  const handleAudit = async () => {
    if (!repoUrl) {
      setError({ hasError: true, message: 'Please enter a repository URL' });
      return;
    }

    if (!pdfPath) {
      setError({
        hasError: true,
        message: 'Please upload a compliance PDF document',
      });
      return;
    }

    try {
      updateCodeAudit({ 
        isLoading: true,
        results: null,
        progressUpdates: [],
        currentProgress: null
      });
      setError({ hasError: false });

      // Use EventSource for SSE
      const eventSource = new EventSource(
        `http://localhost:8000/api/audit/code/stream?` + 
        new URLSearchParams({
          repo_url: repoUrl,
          pdf_path: pdfPath,
          model_name: 'gemini-2.5-flash'
        })
      );

      eventSource.addEventListener('progress', (event) => {
        const data: ProgressUpdate = JSON.parse(event.data);
        updateCodeAudit({ currentProgress: data });
        
        if (data.status === 'file_complete') {
          updateCodeAudit({ 
            progressUpdates: [...progressUpdates, data]
          });
        }
      });

      eventSource.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        updateCodeAudit({ 
          results: data,
          isLoading: false,
          currentProgress: null
        });
        eventSource.close();
      });

      eventSource.addEventListener('error', (event: any) => {
        const errorData = event.data ? JSON.parse(event.data) : {};
        setError({
          hasError: true,
          message: 'Audit failed',
          details: errorData.error || 'Connection error',
        });
        updateCodeAudit({ 
          isLoading: false,
          currentProgress: null
        });
        eventSource.close();
      });

      eventSource.onerror = () => {
        setError({
          hasError: true,
          message: 'Connection failed',
          details: 'Could not connect to server',
        });
        updateCodeAudit({ 
          isLoading: false,
          currentProgress: null
        });
        eventSource.close();
      };

    } catch (err) {
      setError({
        hasError: true,
        message: 'Audit failed',
        details: err instanceof Error ? err.message : 'Unknown error',
      });
      updateCodeAudit({ isLoading: false });
    }
  };

  return (
    <div className="min-h-screen p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4 gradient-text">
            Code Compliance Audit
          </h1>
          <p className="text-gray-600 dark:text-slate-400">
            Scan your repository for compliance violations against regulatory
            documents
          </p>
        </div>

        {/* Input Section */}
        <div className="card mb-8">
          <div className="space-y-6">
            {/* Repository URL */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-700 dark:text-slate-300">
                <Github className="inline w-4 h-4 mr-2" />
                GitHub Repository URL
              </label>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => updateCodeAudit({ repoUrl: e.target.value })}
                placeholder="https://github.com/username/repository"
                className="input-field"
              />
            </div>

            {/* PDF Upload */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-700 dark:text-slate-300">
                <Upload className="inline w-4 h-4 mr-2" />
                Compliance Document (PDF)
              </label>
              <div className="flex items-center gap-4">
                <label className="btn-outline cursor-pointer flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Choose File
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
                {pdfFile && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    {pdfFile.name}
                  </div>
                )}
              </div>
            </div>

            {/* Error Message */}
            {error.hasError && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3">
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

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                onClick={handleAudit}
                disabled={isLoading}
                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    Start Audit
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  resetCodeAudit();
                  setPdfPath('');
                  setError({ hasError: false });
                }}
                disabled={isLoading}
                className="btn-outline disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 px-6"
                title="Clear all fields and results"
              >
                <RotateCcw className="w-5 h-5" />
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Progress Display */}
        {isLoading && currentProgress && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card mb-8"
          >
            <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-slate-200">
              Audit Progress
            </h3>
            
            {/* Current Status */}
            <div className="mb-4 p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg border border-primary-200 dark:border-primary-800">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-primary-600 dark:text-primary-400" />
                <span className="font-medium text-primary-800 dark:text-primary-300">
                  {currentProgress.message}
                </span>
              </div>
              {currentProgress.analyzed_files !== undefined && currentProgress.total_files && (
                <div className="mt-2">
                  <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-300"
                      style={{
                        width: `${(currentProgress.analyzed_files / currentProgress.total_files) * 100}%`
                      }}
                    />
                  </div>
                  <div className="text-sm text-gray-600 dark:text-slate-400 mt-1">
                    {currentProgress.analyzed_files} / {currentProgress.total_files} files analyzed
                  </div>
                </div>
              )}
            </div>

            {/* Completed Files */}
            {progressUpdates.length > 0 && (
              <div className="max-h-64 overflow-y-auto space-y-2">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-2">
                  Analyzed Files:
                </h4>
                <AnimatePresence>
                  {progressUpdates.map((update, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2 text-sm p-2 bg-gray-50 dark:bg-slate-800/50 rounded"
                    >
                      <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                      <span className="flex-1 text-gray-700 dark:text-slate-300 font-mono text-xs">
                        {update.file}
                      </span>
                      {update.violations !== undefined && update.violations > 0 && (
                        <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded text-xs font-semibold">
                          {update.violations} violation{update.violations !== 1 ? 's' : ''}
                        </span>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </motion.div>
        )}

        {/* Results Section */}
        {results && <ViolationResults data={results} />}
      </motion.div>
    </div>
  );
};

export default CodeAudit;
