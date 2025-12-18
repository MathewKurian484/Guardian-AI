import { motion } from 'framer-motion';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  AlertTriangle,
  FileCode,
  Download,
  Shield,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useState } from 'react';
import type { CodeAuditResponse, Violation } from '@/types';

interface ViolationResultsProps {
  data: CodeAuditResponse;
}

const ViolationResults = ({ data }: ViolationResultsProps) => {
  const [expandedViolations, setExpandedViolations] = useState<Set<number>>(
    new Set([0]) // Expand first violation by default
  );

  const violations = data.tool_results.audit_details?.violations || [];
  const totalViolations = violations.length;

  const toggleViolation = (index: number) => {
    setExpandedViolations((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-${Date.now()}.json`;
    a.click();
  };

  // Group violations by rule
  const violationsByRule = violations.reduce((acc, violation) => {
    const rule = violation.rule_violated;
    if (!acc[rule]) {
      acc[rule] = [];
    }
    acc[rule].push(violation);
    return acc;
  }, {} as Record<string, Violation[]>);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Summary Card */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary-500" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-slate-50">
                Audit Results
              </h2>
              <p className="text-sm text-gray-600 dark:text-slate-400">
                {data.tool_results.audit_details?.repository}
              </p>
            </div>
          </div>
          <button onClick={downloadJSON} className="btn-outline flex items-center gap-2">
            <Download className="w-5 h-5" />
            Export JSON
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="text-sm font-semibold text-red-700 dark:text-red-400">
                Violations Found
              </span>
            </div>
            <div className="text-3xl font-bold text-red-600 dark:text-red-400">
              {totalViolations}
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <FileCode className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                Affected Files
              </span>
            </div>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {new Set(violations.map((v) => v.file)).size}
            </div>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-semibold text-purple-700 dark:text-purple-400">
                Rules Violated
              </span>
            </div>
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {Object.keys(violationsByRule).length}
            </div>
          </div>
        </div>
      </div>

      {/* Technical Brief */}
      {data.tool_results.legal_brief && (
        <div className="glass-panel p-6">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-slate-50">
            Compliance Requirements
          </h3>
          <div className="prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
              {data.tool_results.legal_brief}
            </pre>
          </div>
        </div>
      )}

      {/* Violations List */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-slate-50">
          Detected Violations
        </h3>
        {violations.map((violation, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="violation-card"
          >
            <div
              className="flex items-start justify-between cursor-pointer"
              onClick={() => toggleViolation(index)}
            >
              <div className="flex-1">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-bold text-red-600 dark:text-red-400">
                      {index + 1}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-semibold rounded">
                        {violation.rule_violated}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-slate-400">
                        <FileCode className="inline w-4 h-4 mr-1" />
                        {violation.file}
                      </span>
                      <span className="text-sm text-gray-500 dark:text-slate-500">
                        Line {violation.line}
                      </span>
                    </div>
                    <p className="text-gray-700 dark:text-slate-300">
                      {violation.explanation}
                    </p>
                  </div>
                </div>
              </div>
              <button className="flex-shrink-0 ml-4">
                {expandedViolations.has(index) ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>
            </div>

            {expandedViolations.has(index) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-4 pt-4 border-t border-gray-200 dark:border-slate-700"
              >
                <h4 className="text-sm font-semibold mb-2 text-gray-700 dark:text-slate-300">
                  Violating Code:
                </h4>
                <SyntaxHighlighter
                  language="javascript"
                  style={vscDarkPlus}
                  customStyle={{
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                  }}
                >
                  {violation.violating_code}
                </SyntaxHighlighter>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default ViolationResults;
