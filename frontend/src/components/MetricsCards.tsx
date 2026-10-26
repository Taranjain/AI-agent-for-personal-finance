import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  PiggyBank,
  Wallet,
  Scale,
} from 'lucide-react';
import { AnalysisMetrics } from '../lib/api';
import { formatCurrency, formatPercent } from '../lib/utils';

interface MetricsCardsProps {
  metrics?: AnalysisMetrics | null;
  isLoading?: boolean;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm animate-pulse space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="w-8 h-8 bg-slate-200 rounded-lg"></div>
            </div>
            <div className="h-8 bg-slate-200 rounded w-32"></div>
            <div className="h-4 bg-slate-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    );
  }

  // Fallbacks if no metrics loaded yet
  const score = metrics?.health_score ?? 72;
  const savingsRate = metrics?.savings_rate ?? 25.4;
  const cashFlow = metrics?.net_cash_flow ?? 35000;
  const dti = metrics?.debt_to_income ?? 28.0;

  // Visual state evaluations
  const scoreBorder =
    score >= 75
      ? 'border-emerald-200 bg-emerald-50/20'
      : score >= 50
      ? 'border-amber-200 bg-amber-50/20'
      : 'border-rose-200 bg-rose-50/20';

  const savingsBorder =
    savingsRate >= 20
      ? 'border-emerald-200 bg-emerald-50/20'
      : savingsRate >= 10
      ? 'border-amber-200 bg-amber-50/20'
      : 'border-rose-200 bg-rose-50/20';

  const cashFlowBorder =
    cashFlow >= 0 ? 'border-emerald-200 bg-emerald-50/20' : 'border-rose-200 bg-rose-50/20';

  const dtiBorder =
    dti <= 36
      ? 'border-emerald-200 bg-emerald-50/20'
      : dti <= 43
      ? 'border-amber-200 bg-amber-50/20'
      : 'border-rose-200 bg-rose-50/20';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* CARD 1: Financial Health Score */}
      <div
        className={`bg-white rounded-xl border p-4 shadow-sm transition-all hover:shadow-md ${scoreBorder}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Health Score
          </span>
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <ShieldCheck className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline space-x-1">
          <span className="text-2xl font-bold tracking-tight text-slate-900">{score}</span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
        <div className="mt-2 flex items-center text-xs">
          {score >= 75 ? (
            <span className="inline-flex items-center text-emerald-700 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Excellent Health
            </span>
          ) : score >= 50 ? (
            <span className="inline-flex items-center text-amber-700 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Moderate Stability
            </span>
          ) : (
            <span className="inline-flex items-center text-rose-700 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-1" /> Attention Advised
            </span>
          )}
        </div>
      </div>

      {/* CARD 2: Savings Rate */}
      <div
        className={`bg-white rounded-xl border p-4 shadow-sm transition-all hover:shadow-md ${savingsBorder}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Savings Rate
          </span>
          <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
            <PiggyBank className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatPercent(savingsRate)}
          </span>
        </div>
        <div className="mt-2 flex items-center text-xs">
          {savingsRate >= 20 ? (
            <span className="inline-flex items-center text-emerald-700 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Target (20%+) Met
            </span>
          ) : (
            <span className="inline-flex items-center text-amber-700 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-1" /> Below 20% Target
            </span>
          )}
        </div>
      </div>

      {/* CARD 3: Monthly Net Cash Flow */}
      <div
        className={`bg-white rounded-xl border p-4 shadow-sm transition-all hover:shadow-md ${cashFlowBorder}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Monthly Cash Flow
          </span>
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
            <Wallet className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline">
          <span
            className={`text-2xl font-bold tracking-tight ${
              cashFlow >= 0 ? 'text-slate-900' : 'text-rose-600'
            }`}
          >
            {formatCurrency(cashFlow)}
          </span>
        </div>
        <div className="mt-2 flex items-center text-xs">
          {cashFlow >= 0 ? (
            <span className="inline-flex items-center text-emerald-700 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Positive Surplus
            </span>
          ) : (
            <span className="inline-flex items-center text-rose-700 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-1" /> Net Deficit
            </span>
          )}
        </div>
      </div>

      {/* CARD 4: Debt-to-Income Ratio */}
      <div
        className={`bg-white rounded-xl border p-4 shadow-sm transition-all hover:shadow-md ${dtiBorder}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Debt-to-Income
          </span>
          <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
            <Scale className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {formatPercent(dti)}
          </span>
        </div>
        <div className="mt-2 flex items-center text-xs">
          {dti <= 36 ? (
            <span className="inline-flex items-center text-emerald-700 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Healthy (&lt;36%)
            </span>
          ) : dti <= 43 ? (
            <span className="inline-flex items-center text-amber-700 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-1" /> Moderate Load
            </span>
          ) : (
            <span className="inline-flex items-center text-rose-700 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-1" /> Elevated Liability
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
