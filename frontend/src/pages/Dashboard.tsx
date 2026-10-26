import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useAnalysis } from '../hooks/useAnalysis';
import { MetricsCards } from '../components/MetricsCards';
import { ProfileForm } from '../components/ProfileForm';
import { AgentFlowDiagram } from '../components/AgentFlowDiagram';
import { ResultsPanel } from '../components/ResultsPanel';
import { SpendingChart } from '../components/SpendingChart';
import { ChatPanel } from '../components/ChatPanel';
import { Profile } from '../lib/api';
import {
  TrendingUp,
  LogOut,
  Sparkles,
  RefreshCw,
  Bell,
  Cpu,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const { result, isLoading: isAnalyzing, runAnalysis } = useAnalysis();

  // Keep track of current profile inputs to synchronize across spending & metrics
  const [currentProfile, setCurrentProfile] = useState<Profile>({
    age: 28,
    annual_income: 1440000,
    monthly_expenses: 65000,
    savings: 350000,
    risk_tolerance: 'Moderate',
    investment_experience: 'Intermediate',
    time_horizon: 'Medium-term (2-5 yrs)',
  });

  // Run initial analysis automatically on mount to populate dashboard
  useEffect(() => {
    runAnalysis();
  }, []);

  const handleProfileUpdated = useCallback((updated: Profile) => {
    setCurrentProfile(updated);
  }, []);

  const handleRunAnalysis = async () => {
    await runAnalysis({
      analysis_type: 'comprehensive_audit',
      message: 'Analyze current financial profile and generate comprehensive action blueprint.',
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 selection:bg-blue-100 selection:text-blue-900">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200/80 shadow-xs">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-blue-600 text-white shadow-xs">
              <TrendingUp className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-slate-900">FinWise</span>
                <span className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  <Cpu className="w-3 h-3 mr-1 text-blue-600" /> Multi-Agent AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Personal Finance & Wealth Optimization Engine
              </p>
            </div>
          </div>

          {/* User Profile & Actions */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
              className="hidden sm:inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors disabled:opacity-60 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>{isAnalyzing ? 'Analyzing...' : 'Re-run Analysis'}</span>
            </button>

            {/* User Chip */}
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center text-xs font-semibold">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden md:block text-left text-xs">
                <div className="font-semibold text-slate-800 leading-tight">
                  {user?.full_name || 'FinWise User'}
                </div>
                <div className="text-[10px] text-slate-400 truncate max-w-[120px]">
                  {user?.email || 'user@finwise.ai'}
                </div>
              </div>
            </div>

            {/* Logout button */}
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <div className="max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 flex flex-col lg:flex-row gap-6">
        {/* LEFT SIDEBAR (320px Desktop) */}
        <aside className="w-full lg:w-[340px] flex-shrink-0 space-y-6">
          {/* Profile Form */}
          <ProfileForm
            onAnalyze={handleRunAnalysis}
            isAnalyzing={isAnalyzing}
            onProfileUpdated={handleProfileUpdated}
          />

          {/* Educational Chat Assistant */}
          <ChatPanel />
        </aside>

        {/* RIGHT MAIN AREA */}
        <main className="flex-1 min-w-0 space-y-6">
          {/* TOP ROW: Metrics Cards */}
          <section>
            <MetricsCards
              metrics={result?.metrics}
              isLoading={isAnalyzing && !result}
            />
          </section>

          {/* MIDDLE ROW: Agent Flow Diagram + Financial Plan */}
          <section className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            {/* Agent Flow Diagram (5 cols) */}
            <div className="xl:col-span-5 flex flex-col">
              <AgentFlowDiagram
                workflowTrace={result?.workflow_trace}
                isAnalyzing={isAnalyzing}
              />
            </div>

            {/* Financial Plan Results Panel (7 cols) */}
            <div className="xl:col-span-7 flex flex-col">
              <ResultsPanel
                planMarkdown={result?.plan_markdown}
                insights={result?.insights}
                isLoading={isAnalyzing && !result}
              />
            </div>
          </section>

          {/* BOTTOM ROW: Spending Chart (Budget Allocation) */}
          <section>
            <SpendingChart
              monthlyIncome={Math.round(currentProfile.annual_income / 12)}
              monthlyExpenses={currentProfile.monthly_expenses}
            />
          </section>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">FinWise AI</span>
            <span>&bull;</span>
            <span>Deterministic Financial Engine with Multi-Agent Synthesis</span>
          </div>
          <div className="text-[11px] text-slate-400">
            All calculations verified with strict mathematical guardrails
          </div>
        </div>
      </footer>
    </div>
  );
};
