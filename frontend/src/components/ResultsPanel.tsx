import React, { useState } from 'react';
import {
  FileText,
  Copy,
  Check,
  AlertTriangle,
  Lightbulb,
  CheckCircle,
  Info,
  Sparkles,
} from 'lucide-react';
import { AnalysisInsight } from '../lib/api';

interface ResultsPanelProps {
  planMarkdown?: string | null;
  insights?: AnalysisInsight[];
  isLoading?: boolean;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({
  planMarkdown,
  insights = [],
  isLoading = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!planMarkdown) return;
    navigator.clipboard.writeText(planMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper to parse simple markdown formatting into React elements safely
  const renderMarkdown = (content: string) => {
    const lines = content.split('\n');

    return lines.map((line, idx) => {
      const trimmed = line.trim();

      // Heading 1
      if (trimmed.startsWith('# ')) {
        const text = trimmed.slice(2);
        return (
          <h1 key={idx} className="text-lg font-bold text-slate-900 mt-4 mb-2">
            {parseInlineStyles(text)}
          </h1>
        );
      }

      // Heading 2
      if (trimmed.startsWith('## ')) {
        const text = trimmed.slice(3);
        return (
          <h2
            key={idx}
            className="text-base font-bold text-slate-800 mt-5 mb-2 pb-1 border-b border-slate-100 flex items-center space-x-2"
          >
            <span>{parseInlineStyles(text)}</span>
          </h2>
        );
      }

      // Heading 3
      if (trimmed.startsWith('### ')) {
        const text = trimmed.slice(4);
        return (
          <h3 key={idx} className="text-sm font-semibold text-slate-800 mt-3 mb-1">
            {parseInlineStyles(text)}
          </h3>
        );
      }

      // Unordered list item (- or *)
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const text = trimmed.slice(2);
        return (
          <li key={idx} className="flex items-start space-x-2 text-xs text-slate-700 my-1 ml-1 leading-relaxed">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></span>
            <span>{parseInlineStyles(text)}</span>
          </li>
        );
      }

      // Ordered list item (1. 2. etc.)
      const orderedMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (orderedMatch) {
        const num = orderedMatch[1];
        const text = orderedMatch[2];
        return (
          <div key={idx} className="flex items-start space-x-2 text-xs text-slate-700 my-1 ml-1 leading-relaxed">
            <span className="font-semibold text-blue-600 min-w-[16px] text-right flex-shrink-0">
              {num}.
            </span>
            <span>{parseInlineStyles(text)}</span>
          </div>
        );
      }

      // Blank line
      if (trimmed === '') {
        return <div key={idx} className="h-2" />;
      }

      // Standard paragraph
      return (
        <p key={idx} className="text-xs text-slate-600 leading-relaxed my-1">
          {parseInlineStyles(trimmed)}
        </p>
      );
    });
  };

  // Parses **bold** and `code` tags inline
  const parseInlineStyles = (text: string): React.ReactNode => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);

    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={index} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={index}
            className="px-1 py-0.5 rounded bg-slate-100 text-blue-700 font-mono text-[11px]"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />;
      case 'action':
        return <Lightbulb className="w-4 h-4 text-blue-600 flex-shrink-0" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-slate-600 flex-shrink-0" />;
    }
  };

  const getInsightStyle = (type: string) => {
    switch (type) {
      case 'warning':
        return 'bg-amber-50/70 border-amber-200 text-amber-900';
      case 'action':
        return 'bg-blue-50/70 border-blue-200 text-blue-900';
      case 'success':
        return 'bg-emerald-50/70 border-emerald-200 text-emerald-900';
      default:
        return 'bg-slate-50 border-slate-200 text-slate-800';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full max-h-[560px]">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-800">Synthesized Financial Blueprint</h3>
        </div>
        {planMarkdown && (
          <button
            onClick={handleCopy}
            className="inline-flex items-center space-x-1 text-xs text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50 px-2.5 py-1 rounded-lg transition-colors shadow-xs"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy Plan</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Content Area */}
      <div className="p-5 overflow-y-auto flex-1 space-y-5">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-6 bg-slate-200 rounded w-1/3"></div>
            <div className="h-4 bg-slate-200 rounded w-full"></div>
            <div className="h-4 bg-slate-200 rounded w-5/6"></div>
            <div className="h-20 bg-slate-100 rounded-lg"></div>
            <div className="h-4 bg-slate-200 rounded w-4/6"></div>
          </div>
        ) : planMarkdown ? (
          <div>
            <div className="prose-sm">{renderMarkdown(planMarkdown)}</div>

            {/* AI Insights Callout Cards */}
            {insights && insights.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-100 space-y-3">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Agent Key Takeaways & Recommendations</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {insights.map((insight, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border flex items-start space-x-2.5 ${getInsightStyle(
                        insight.actionType
                      )}`}
                    >
                      {getInsightIcon(insight.actionType)}
                      <div className="min-w-0">
                        <div className="flex items-center space-x-1.5 mb-0.5">
                          <span className="text-[10px] font-semibold uppercase tracking-wide opacity-75">
                            [{insight.agent}]
                          </span>
                        </div>
                        <h5 className="text-xs font-semibold leading-tight">{insight.title}</h5>
                        <p className="text-[11px] mt-1 leading-normal opacity-90">
                          {insight.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3 text-slate-400">
              <FileText className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-medium text-slate-700">No Plan Generated Yet</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Review your financial profile on the left sidebar and click &ldquo;Analyze My Finances&rdquo; to execute the multi-agent reasoning pipeline.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
