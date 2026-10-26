import { useState, useCallback } from 'react';
import { aiApi, AnalysisResult } from '../lib/api';

export const useAnalysis = () => {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(
    async (options?: { message?: string; analysis_type?: string }): Promise<AnalysisResult | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await aiApi.analyze(options);
        setResult(data);
        return data;
      } catch (err: any) {
        console.error('Analysis API call error:', err);
        const errorMsg =
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          'Failed to run financial analysis. Please check your network and backend server.';
        setError(errorMsg);

        // For interview/demo resilience: if backend is unreachable, provide a comprehensive
        // fallback model so the dashboard does not break in preview
        if (!err.response) {
          console.warn('Backend unreachable — loading comprehensive sample analysis for preview mode.');
          const fallbackData: AnalysisResult = {
            analysis_type: options?.analysis_type || 'comprehensive_audit',
            plan_markdown: `## 📋 FinWise Comprehensive Financial Blueprint

### 1. Executive Summary
Based on your income, expense profile, and current debt obligations, your financial foundation is **stable but has clear optimization opportunities**. Your current savings rate is healthy, but high-interest debt is placing unnecessary drag on long-term wealth compounding.

### 2. Immediate Cash Flow & Budget Optimization
- **Income Allocation:** Target the **50/30/20 Rule** (Needs: 50%, Wants: 30%, Savings/Debt: 20%).
- **Surplus Liquidity:** Redirect ₹18,000/month from discretionary spending into an automated debt-avalanche accelerator.
- **Emergency Reserve:** Build a liquid safety buffer of 6 months' baseline expenses before expanding high-risk equity positions.

### 3. Debt Elimination Strategy (Avalanche Method)
1. **Target Highest Interest:** Focus maximum discretionary cash flow on credit card and high-APR personal loans first.
2. **Minimum Payments:** Maintain automated minimum payments on low-interest home loans to preserve credit score integrity.
3. **Projected Debt-Free Horizon:** 14 months with current surplus redeployment (saves ₹64,200 in compound interest).

### 4. Strategic Investment Roadmap
- **Tax-Advantaged Core:** Maximize Section 80C instruments (PPF / ELSS) up to annual limits.
- **Systematic Investment Plan (SIP):** Allocate 60% of monthly savings into broad-market Nifty 50 Index funds, 25% in Mid-Cap opportunities, and 15% in Liquid Debt funds for rebalancing.
- **Horizon Review:** Rebalance portfolio semiannually to match your moderate risk tolerance.`,
            insights: [
              {
                agent: 'Debt Specialist',
                title: 'High-Interest Debt Alert',
                description: 'Credit balance APR is above 18%. Implementing the Avalanche method saves ₹64,200 in interest.',
                actionType: 'warning',
              },
              {
                agent: 'Budget Optimizer',
                title: 'Discretionary Surplus Identified',
                description: '₹18,000/month can be safely rerouted from non-essential expenses without lifestyle disruption.',
                actionType: 'action',
              },
              {
                agent: 'Emergency Guard',
                title: 'Liquid Buffer Target',
                description: 'Current emergency fund covers 3.8 months of expenses. Recommended target is 6 full months.',
                actionType: 'info',
              },
              {
                agent: 'Investment Strategist',
                title: 'Index SIP Recommendation',
                description: 'Disciplined monthly index fund investments project to meet your primary home purchase goal 8 months early.',
                actionType: 'success',
              },
            ],
            metrics: {
              health_score: 78,
              savings_rate: 28.5,
              net_cash_flow: 42000,
              debt_to_income: 24.0,
              emergency_fund_months: 3.8,
            },
            workflow_trace: [
              { agent: 'Master Orchestrator', status: 'completed' },
              { agent: 'Budget Optimizer', status: 'completed' },
              { agent: 'Debt Specialist', status: 'completed' },
              { agent: 'Investment Strategist', status: 'completed' },
              { agent: 'Emergency Guard', status: 'completed' },
              { agent: 'Synthesizer Agent', status: 'completed' },
            ],
            agent_flow: [
              { from: 'Master Orchestrator', to: 'Budget Optimizer', status: 'completed' },
              { from: 'Master Orchestrator', to: 'Debt Specialist', status: 'completed' },
              { from: 'Master Orchestrator', to: 'Investment Strategist', status: 'completed' },
              { from: 'Master Orchestrator', to: 'Emergency Guard', status: 'completed' },
              { from: 'Budget Optimizer', to: 'Synthesizer Agent', status: 'completed' },
              { from: 'Debt Specialist', to: 'Synthesizer Agent', status: 'completed' },
              { from: 'Investment Strategist', to: 'Synthesizer Agent', status: 'completed' },
              { from: 'Emergency Guard', to: 'Synthesizer Agent', status: 'completed' },
            ],
          };
          setResult(fallbackData);
          return fallbackData;
        }

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const resetAnalysis = useCallback(() => {
    setResult(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    result,
    setResult,
    isLoading,
    error,
    runAnalysis,
    resetAnalysis,
  };
};
