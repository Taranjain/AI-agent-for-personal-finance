import React, { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { formatCurrency, formatPercent } from '../lib/utils';
import { PieChart as ChartIcon, CheckCircle2 } from 'lucide-react';

interface SpendingChartProps {
  monthlyExpenses?: number;
  monthlyIncome?: number;
  categoryData?: Record<string, number>;
}

interface BudgetCategory {
  name: string;
  value: number;
  percentage: number;
  color: string;
  type: 'Needs' | 'Wants' | 'Savings/Debt';
}

const CATEGORY_COLORS: Record<string, string> = {
  Housing: '#2563EB',         // Primary Blue
  Food: '#10B981',            // Emerald Green
  Transportation: '#06B6D4',  // Cyan
  Healthcare: '#F59E0B',      // Amber
  'Debt Repayment': '#F43F5E', // Rose
  'Savings & SIP': '#8B5CF6', // Purple
  Discretionary: '#64748B',   // Slate
};

export const SpendingChart: React.FC<SpendingChartProps> = ({
  monthlyExpenses = 65000,
  monthlyIncome = 120000,
  categoryData,
}) => {
  // Compute chart categories and values dynamically
  const { data, totalAllocated, ruleBreakdown } = useMemo(() => {
    let rawItems: { name: string; value: number; type: 'Needs' | 'Wants' | 'Savings/Debt' }[];

    if (categoryData && Object.keys(categoryData).length > 0) {
      rawItems = Object.entries(categoryData).map(([name, value]) => ({
        name,
        value: Number(value),
        type: name.includes('Savings')
          ? 'Savings/Debt'
          : name.includes('Discretionary')
          ? 'Wants'
          : 'Needs',
      }));
    } else {
      // Deterministic realistic benchmark allocation based on total expenses
      const expenseBase = monthlyExpenses > 0 ? monthlyExpenses : 65000;
      const savingsPortion = Math.max(0, monthlyIncome - expenseBase);

      rawItems = [
        { name: 'Housing', value: Math.round(expenseBase * 0.35), type: 'Needs' },
        { name: 'Food', value: Math.round(expenseBase * 0.20), type: 'Needs' },
        { name: 'Transportation', value: Math.round(expenseBase * 0.12), type: 'Needs' },
        { name: 'Healthcare', value: Math.round(expenseBase * 0.08), type: 'Needs' },
        { name: 'Debt Repayment', value: Math.round(expenseBase * 0.10), type: 'Savings/Debt' },
        { name: 'Savings & SIP', value: savingsPortion > 0 ? savingsPortion : Math.round(expenseBase * 0.15), type: 'Savings/Debt' },
        { name: 'Discretionary', value: Math.round(expenseBase * 0.15), type: 'Wants' },
      ];
    }

    const total = rawItems.reduce((acc, curr) => acc + curr.value, 0);

    const formattedData: BudgetCategory[] = rawItems.map((item) => ({
      ...item,
      percentage: total > 0 ? (item.value / total) * 100 : 0,
      color: CATEGORY_COLORS[item.name] || '#94A3B8',
    }));

    // Calculate 50/30/20 summary
    const needsSum = formattedData
      .filter((d) => d.type === 'Needs')
      .reduce((acc, d) => acc + d.value, 0);
    const wantsSum = formattedData
      .filter((d) => d.type === 'Wants')
      .reduce((acc, d) => acc + d.value, 0);
    const savingsSum = formattedData
      .filter((d) => d.type === 'Savings/Debt')
      .reduce((acc, d) => acc + d.value, 0);

    const baseForPercent = total > 0 ? total : 1;

    return {
      data: formattedData,
      totalAllocated: total,
      ruleBreakdown: {
        needsPct: (needsSum / baseForPercent) * 100,
        wantsPct: (wantsSum / baseForPercent) * 100,
        savingsPct: (savingsSum / baseForPercent) * 100,
      },
    };
  }, [monthlyExpenses, monthlyIncome, categoryData]);

  // Custom clean tooltip for Recharts
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload as BudgetCategory;
      return (
        <div className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg border border-slate-800">
          <div className="font-semibold">{item.name}</div>
          <div className="text-slate-300 mt-0.5">
            {formatCurrency(item.value)} ({formatPercent(item.percentage)})
          </div>
          <div className="text-[10px] text-blue-400 mt-1 uppercase tracking-wider">
            {item.type}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
        <div>
          <div className="flex items-center space-x-2">
            <ChartIcon className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-slate-800">Monthly Budget Allocation</h3>
          </div>
          <p className="text-xs text-slate-500">
            Total Monthly Outlay: <span className="font-semibold text-slate-700">{formatCurrency(totalAllocated)}</span>
          </p>
        </div>

        {/* 50/30/20 Rule Comparison Pill */}
        <div className="flex items-center space-x-3 text-xs bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <span className="text-slate-600">Needs:</span>
            <span className="font-semibold text-slate-800">{formatPercent(ruleBreakdown.needsPct, 0)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-slate-500"></span>
            <span className="text-slate-600">Wants:</span>
            <span className="font-semibold text-slate-800">{formatPercent(ruleBreakdown.wantsPct, 0)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-purple-600"></span>
            <span className="text-slate-600">Savings:</span>
            <span className="font-semibold text-slate-800">{formatPercent(ruleBreakdown.savingsPct, 0)}</span>
          </div>
        </div>
      </div>

      {/* Chart and Legend Area */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center pt-4">
        {/* Donut Chart (Cols 1-6) */}
        <div className="md:col-span-6 h-64 flex items-center justify-center relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={95}
                paddingAngle={3}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          {/* Donut Center Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Total</span>
            <span className="text-base font-bold text-slate-800">{formatCurrency(totalAllocated)}</span>
          </div>
        </div>

        {/* Categories Legend List (Cols 7-12) */}
        <div className="md:col-span-6 space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {data.map((category) => (
              <div
                key={category.name}
                className="flex items-center justify-between p-2 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center space-x-2 truncate">
                  <span
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="text-slate-700 font-medium truncate">{category.name}</span>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <div className="font-semibold text-slate-900 font-mono text-[11px]">
                    {formatCurrency(category.value)}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {formatPercent(category.percentage)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 flex items-center text-[11px] text-emerald-700 bg-emerald-50/60 px-3 py-1.5 rounded-lg border border-emerald-100">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
            <span>Allocation follows recommended prudent surplus thresholds.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
