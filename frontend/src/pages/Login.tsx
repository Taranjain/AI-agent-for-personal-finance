import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  TrendingUp,
  ShieldCheck,
  Zap,
  ArrowRight,
  Loader2,
  AlertCircle,
  Eye,
  EyeOff,
} from 'lucide-react';

export const Login: React.FC = () => {
  const { login, register, error, clearError } = useAuth();

  const [isRegisterTab, setIsRegisterTab] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Form states
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('demo@finwise.ai');
  const [password, setPassword] = useState('password123');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError('Please fill in all required fields.');
      return;
    }

    if (isRegisterTab && !fullName.trim()) {
      setLocalError('Please enter your full name.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (isRegisterTab) {
        await register({ email, password, full_name: fullName });
      } else {
        await login({ email, password });
      }
    } catch (err: any) {
      // Error is caught and stored in auth context or local error
      setLocalError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-blue-100 selection:text-blue-900">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-500/20 mb-4">
          <TrendingUp className="w-6 h-6 stroke-[2.5]" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">FinWise</h1>
        <p className="mt-1 text-sm text-slate-500">
          Autonomous AI-Powered Personal Finance & Wealth Optimization
        </p>
      </div>

      {/* Main Card */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10">
          {/* Tab Selector */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => {
                setIsRegisterTab(false);
                setLocalError(null);
                clearError();
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                !isRegisterTab
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setIsRegisterTab(true);
                setLocalError(null);
                clearError();
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                isRegisterTab
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error Banner */}
          {(localError || error) && (
            <div className="mb-5 p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-700 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{localError || error}</span>
            </div>
          )}

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            {isRegisterTab && (
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Sharma"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-medium text-slate-700">
                  Password
                </label>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors pr-9"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold shadow-sm hover:shadow transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <>
                    <span>{isRegisterTab ? 'Create FinWise Account' : 'Sign In to Dashboard'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Demo Info Box */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-[11px] text-slate-600 space-y-1">
              <div className="flex items-center text-slate-700 font-semibold space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                <span>Demo Access</span>
              </div>
              <p className="text-slate-500">
                Default credentials are pre-filled for immediate testing:
              </p>
              <div className="font-mono text-[10px] text-slate-700 bg-white p-1.5 rounded border border-slate-200">
                demo@finwise.ai / password123
              </div>
            </div>
          </div>
        </div>

        {/* Feature Badges */}
        <div className="mt-8 grid grid-cols-3 gap-2 text-center text-slate-500 text-[11px]">
          <div className="p-2">
            <Zap className="w-4 h-4 mx-auto text-blue-600 mb-1" />
            <span>Multi-Agent LangGraph</span>
          </div>
          <div className="p-2">
            <ShieldCheck className="w-4 h-4 mx-auto text-emerald-600 mb-1" />
            <span>Deterministic Math</span>
          </div>
          <div className="p-2">
            <TrendingUp className="w-4 h-4 mx-auto text-indigo-600 mb-1" />
            <span>Tailored Strategies</span>
          </div>
        </div>
      </div>
    </div>
  );
};
