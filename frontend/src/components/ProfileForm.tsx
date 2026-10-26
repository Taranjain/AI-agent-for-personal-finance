import React, { useState, useEffect } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
  User,
  CreditCard,
  Target,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { Profile, Debt, Goal, profileApi, debtsApi, goalsApi } from '../lib/api';

interface ProfileFormProps {
  onAnalyze: () => Promise<void>;
  isAnalyzing: boolean;
  onProfileUpdated?: (profile: Profile) => void;
}

export const ProfileForm: React.FC<ProfileFormProps> = ({
  onAnalyze,
  isAnalyzing,
  onProfileUpdated,
}) => {
  // Collapsible accordion states
  const [basicOpen, setBasicOpen] = useState(true);
  const [debtsOpen, setDebtsOpen] = useState(true);
  const [goalsOpen, setGoalsOpen] = useState(true);

  // Form states
  const [profile, setProfile] = useState<Profile>({
    age: 28,
    annual_income: 1440000,
    monthly_expenses: 65000,
    savings: 350000,
    risk_tolerance: 'Moderate',
    investment_experience: 'Intermediate',
    time_horizon: 'Medium-term (2-5 yrs)',
  });

  const [debts, setDebts] = useState<Debt[]>([
    {
      name: 'Credit Card Outstanding',
      debt_type: 'Credit Card',
      balance: 45000,
      interest_rate: 36.0,
      minimum_payment: 2500,
    },
    {
      name: 'Car Loan',
      debt_type: 'Auto Loan',
      balance: 380000,
      interest_rate: 8.8,
      minimum_payment: 12000,
    },
  ]);

  const [goals, setGoals] = useState<Goal[]>([
    {
      name: 'Emergency Fund',
      target_amount: 400000,
      timeline_months: 12,
      priority: 5,
      current_amount: 150000,
    },
    {
      name: 'Home Down Payment',
      target_amount: 2500000,
      timeline_months: 48,
      priority: 4,
      current_amount: 200000,
    },
  ]);

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch initial profile data on mount
  useEffect(() => {
    let isMounted = true;
    const loadProfileData = async () => {
      try {
        const [fetchedProfile, fetchedDebts, fetchedGoals] = await Promise.allSettled([
          profileApi.getProfile(),
          debtsApi.getDebts(),
          goalsApi.getGoals(),
        ]);

        if (!isMounted) return;

        if (fetchedProfile.status === 'fulfilled' && fetchedProfile.value) {
          setProfile(fetchedProfile.value);
          if (onProfileUpdated) onProfileUpdated(fetchedProfile.value);
        }

        if (fetchedDebts.status === 'fulfilled' && Array.isArray(fetchedDebts.value) && fetchedDebts.value.length > 0) {
          setDebts(fetchedDebts.value);
        }

        if (fetchedGoals.status === 'fulfilled' && Array.isArray(fetchedGoals.value) && fetchedGoals.value.length > 0) {
          setGoals(fetchedGoals.value);
        }
      } catch (err) {
        console.warn('Using initial profile baseline data:', err);
      }
    };

    loadProfileData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Handlers for Basic Profile
  const handleProfileChange = (field: keyof Profile, value: any) => {
    setProfile((prev) => {
      const updated = { ...prev, [field]: value };
      if (onProfileUpdated) onProfileUpdated(updated);
      return updated;
    });
  };

  // Handlers for Debts
  const handleAddDebt = () => {
    setDebts((prev) => [
      ...prev,
      {
        name: 'New Debt',
        debt_type: 'Personal Loan',
        balance: 50000,
        interest_rate: 12.0,
        minimum_payment: 3000,
      },
    ]);
  };

  const handleUpdateDebt = (index: number, field: keyof Debt, value: any) => {
    setDebts((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleRemoveDebt = (index: number) => {
    setDebts((prev) => prev.filter((_, i) => i !== index));
  };

  // Handlers for Goals
  const handleAddGoal = () => {
    setGoals((prev) => [
      ...prev,
      {
        name: 'New Financial Goal',
        target_amount: 100000,
        timeline_months: 12,
        priority: 3,
        current_amount: 0,
      },
    ]);
  };

  const handleUpdateGoal = (index: number, field: keyof Goal, value: any) => {
    setGoals((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleRemoveGoal = (index: number) => {
    setGoals((prev) => prev.filter((_, i) => i !== index));
  };

  // Submit and trigger analysis
  const handleSubmitAndAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSaving(true);

    try {
      // Validate
      if (profile.annual_income <= 0) {
        throw new Error('Annual income must be greater than 0');
      }
      if (profile.monthly_expenses < 0) {
        throw new Error('Monthly expenses cannot be negative');
      }

      // Persist profile to backend
      try {
        await profileApi.updateProfile(profile);
      } catch (err) {
        console.warn('Profile sync fallback:', err);
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);

      // Trigger agent analysis
      await onAnalyze();
    } catch (err: any) {
      setFormError(err.message || 'Validation error');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
        <div>
          <h2 className="text-sm font-semibold text-slate-800">Financial Profile</h2>
          <p className="text-xs text-slate-500">Inputs driving the multi-agent AI pipeline</p>
        </div>
        {saveSuccess && (
          <span className="inline-flex items-center text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSubmitAndAnalyze} className="divide-y divide-slate-100">
        {formError && (
          <div className="p-3 bg-rose-50 border-b border-rose-100 flex items-center text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        {/* SECTION 1: Basic Info */}
        <div>
          <button
            type="button"
            onClick={() => setBasicOpen(!basicOpen)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-50/60 transition-colors"
          >
            <div className="flex items-center space-x-2 text-slate-700">
              <User className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold uppercase tracking-wider">Basic Information</span>
            </div>
            {basicOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>

          {basicOpen && (
            <div className="px-4 pb-4 pt-1 space-y-3 bg-white">
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Age</label>
                  <input
                    type="number"
                    min={18}
                    max={100}
                    value={profile.age}
                    onChange={(e) => handleProfileChange('age', parseInt(e.target.value) || 0)}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Annual Income (₹)</label>
                  <input
                    type="number"
                    step={1000}
                    min={0}
                    value={profile.annual_income}
                    onChange={(e) => handleProfileChange('annual_income', parseFloat(e.target.value) || 0)}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-mono"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Monthly Expenses (₹)</label>
                  <input
                    type="number"
                    step={500}
                    min={0}
                    value={profile.monthly_expenses}
                    onChange={(e) => handleProfileChange('monthly_expenses', parseFloat(e.target.value) || 0)}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Current Savings (₹)</label>
                  <input
                    type="number"
                    step={1000}
                    min={0}
                    value={profile.savings}
                    onChange={(e) => handleProfileChange('savings', parseFloat(e.target.value) || 0)}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-mono"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">Risk Tolerance</label>
                <select
                  value={profile.risk_tolerance}
                  onChange={(e) => handleProfileChange('risk_tolerance', e.target.value as any)}
                  className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="Conservative">Conservative (Capital Preservation)</option>
                  <option value="Moderate">Moderate (Balanced Growth)</option>
                  <option value="Aggressive">Aggressive (High Equity / Maximum Wealth)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Investment Exp.</label>
                  <select
                    value={profile.investment_experience}
                    onChange={(e) => handleProfileChange('investment_experience', e.target.value as any)}
                    className="w-full text-xs px-2 py-1.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Horizon</label>
                  <select
                    value={profile.time_horizon}
                    onChange={(e) => handleProfileChange('time_horizon', e.target.value as any)}
                    className="w-full text-xs px-2 py-1.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Short-term (<2 yrs)">Short (&lt;2 yrs)</option>
                    <option value="Medium-term (2-5 yrs)">Medium (2-5 yrs)</option>
                    <option value="Long-term (5+ yrs)">Long (5+ yrs)</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 2: Debts */}
        <div>
          <button
            type="button"
            onClick={() => setDebtsOpen(!debtsOpen)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-50/60 transition-colors"
          >
            <div className="flex items-center space-x-2 text-slate-700">
              <CreditCard className="w-4 h-4 text-rose-500" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Debts & Liabilities ({debts.length})
              </span>
            </div>
            {debtsOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>

          {debtsOpen && (
            <div className="px-4 pb-4 pt-1 space-y-3 bg-white">
              {debts.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-1">No active debts registered.</p>
              ) : (
                debts.map((debt, index) => (
                  <div
                    key={index}
                    className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2 relative group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <input
                        type="text"
                        value={debt.name}
                        placeholder="Debt name"
                        onChange={(e) => handleUpdateDebt(index, 'name', e.target.value)}
                        className="text-xs font-medium px-2 py-1 rounded border border-slate-200 bg-white flex-1 focus:ring-1 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveDebt(index)}
                        className="text-slate-400 hover:text-rose-600 transition-colors p-1"
                        title="Remove debt"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-3 gap-1.5 text-[11px]">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Type</span>
                        <select
                          value={debt.debt_type}
                          onChange={(e) => handleUpdateDebt(index, 'debt_type', e.target.value as any)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white"
                        >
                          <option value="Credit Card">Card</option>
                          <option value="Personal Loan">Personal</option>
                          <option value="Auto Loan">Auto</option>
                          <option value="Home Loan">Home</option>
                          <option value="Student Loan">Student</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Balance (₹)</span>
                        <input
                          type="number"
                          value={debt.balance}
                          onChange={(e) => handleUpdateDebt(index, 'balance', parseFloat(e.target.value) || 0)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white font-mono"
                        />
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">APR (%)</span>
                        <input
                          type="number"
                          step={0.1}
                          value={debt.interest_rate}
                          onChange={(e) => handleUpdateDebt(index, 'interest_rate', parseFloat(e.target.value) || 0)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white font-mono"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}

              <button
                type="button"
                onClick={handleAddDebt}
                className="w-full py-1.5 px-3 border border-dashed border-slate-300 rounded-lg text-xs font-medium text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors flex items-center justify-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Liability</span>
              </button>
            </div>
          )}
        </div>

        {/* SECTION 3: Goals */}
        <div>
          <button
            type="button"
            onClick={() => setGoalsOpen(!goalsOpen)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-50/60 transition-colors"
          >
            <div className="flex items-center space-x-2 text-slate-700">
              <Target className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Financial Goals ({goals.length})
              </span>
            </div>
            {goalsOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>

          {goalsOpen && (
            <div className="px-4 pb-4 pt-1 space-y-3 bg-white">
              {goals.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-1">No active goals set.</p>
              ) : (
                goals.map((goal, index) => (
                  <div
                    key={index}
                    className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <input
                        type="text"
                        value={goal.name}
                        placeholder="Goal title"
                        onChange={(e) => handleUpdateGoal(index, 'name', e.target.value)}
                        className="text-xs font-medium px-2 py-1 rounded border border-slate-200 bg-white flex-1 focus:ring-1 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveGoal(index)}
                        className="text-slate-400 hover:text-rose-600 transition-colors p-1"
                        title="Remove goal"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-3 gap-1.5 text-[11px]">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Target (₹)</span>
                        <input
                          type="number"
                          step={5000}
                          value={goal.target_amount}
                          onChange={(e) => handleUpdateGoal(index, 'target_amount', parseFloat(e.target.value) || 0)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white font-mono"
                        />
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Months</span>
                        <input
                          type="number"
                          value={goal.timeline_months}
                          onChange={(e) => handleUpdateGoal(index, 'timeline_months', parseInt(e.target.value) || 1)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white font-mono"
                        />
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Priority (1-5)</span>
                        <input
                          type="number"
                          min={1}
                          max={5}
                          value={goal.priority}
                          onChange={(e) => handleUpdateGoal(index, 'priority', parseInt(e.target.value) || 1)}
                          className="w-full px-1.5 py-1 text-[11px] rounded border border-slate-200 bg-white font-mono"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}

              <button
                type="button"
                onClick={handleAddGoal}
                className="w-full py-1.5 px-3 border border-dashed border-slate-300 rounded-lg text-xs font-medium text-slate-600 hover:text-emerald-600 hover:border-emerald-300 transition-colors flex items-center justify-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Goal</span>
              </button>
            </div>
          )}
        </div>

        {/* Submit & Action Button */}
        <div className="p-4 bg-slate-50/70">
          <button
            type="submit"
            disabled={isAnalyzing || isSaving}
            className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium text-xs shadow-sm hover:shadow transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
          >
            {isAnalyzing || isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Multi-Agent Analysis...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Analyze My Finances</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
