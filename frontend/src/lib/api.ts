import axios, { AxiosError } from 'axios';

// Base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('finwise_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle unauthenticated responses
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('finwise_token');
      localStorage.removeItem('finwise_user');
      // If needed, can trigger an event or redirect
    }
    return Promise.reject(error);
  }
);

/* =========================================================================
   Types and Data Interfaces
   ========================================================================= */

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface Profile {
  id?: string;
  user_id?: string;
  age: number;
  annual_income: number;
  monthly_expenses: number;
  savings: number;
  risk_tolerance: 'Conservative' | 'Moderate' | 'Aggressive';
  investment_experience: 'Beginner' | 'Intermediate' | 'Advanced';
  time_horizon: 'Short-term (<2 yrs)' | 'Medium-term (2-5 yrs)' | 'Long-term (5+ yrs)';
  updated_at?: string;
}

export interface Debt {
  id?: string;
  name: string;
  debt_type: 'Credit Card' | 'Personal Loan' | 'Home Loan' | 'Auto Loan' | 'Student Loan' | 'Other';
  balance: number;
  interest_rate: number;
  minimum_payment: number;
}

export interface Goal {
  id?: string;
  name: string;
  target_amount: number;
  timeline_months: number;
  priority: number; // 1 to 5
  current_amount?: number;
}

export interface Transaction {
  id?: string;
  amount: number;
  category: string;
  type: 'income' | 'expense';
  description: string;
  date: string;
}

export interface TransactionSummary {
  total_income: number;
  total_expenses: number;
  net_cash_flow: number;
  by_category: Record<string, number>;
}

export interface AnalysisInsight {
  agent: string;
  title: string;
  description: string;
  actionType: 'warning' | 'info' | 'success' | 'action';
}

export interface AnalysisMetrics {
  health_score: number;
  savings_rate: number;
  net_cash_flow: number;
  debt_to_income: number;
  emergency_fund_months: number;
}

export interface WorkflowTraceStep {
  agent: string;
  startedAt?: string;
  endedAt?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | string;
}

export interface AgentFlowEdge {
  from: string;
  to: string;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | string;
}

export interface AnalysisResult {
  analysis_type: string;
  plan_markdown: string;
  insights: AnalysisInsight[];
  metrics: AnalysisMetrics;
  workflow_trace: WorkflowTraceStep[];
  agent_flow: (AgentFlowEdge | string)[];
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

/* =========================================================================
   API Methods
   ========================================================================= */

// Auth Endpoints
export const authApi = {
  register: async (payload: { email: string; password: string; full_name: string }): Promise<AuthResponse> => {
    const res = await api.post<AuthResponse>('/api/auth/register', payload);
    return res.data;
  },

  login: async (payload: { email: string; password: string }): Promise<AuthResponse> => {
    const res = await api.post<AuthResponse>('/api/auth/login', payload);
    return res.data;
  },

  getCurrentUser: async (): Promise<{ user: User }> => {
    const res = await api.get<{ user?: User } | User>('/api/auth/me');
    // Normalize response if user object is returned directly or inside { user: ... }
    if ('user' in res.data && res.data.user) {
      return { user: res.data.user };
    }
    return { user: res.data as User };
  },
};

// Profile Endpoints
export const profileApi = {
  getProfile: async (): Promise<Profile> => {
    const res = await api.get<Profile>('/api/profile');
    return res.data;
  },

  updateProfile: async (payload: Partial<Profile>): Promise<Profile> => {
    const res = await api.put<Profile>('/api/profile', payload);
    return res.data;
  },

  setupProfile: async (payload: {
    profile: Partial<Profile>;
    debts: Omit<Debt, 'id'>[];
    goals: Omit<Goal, 'id' | 'current_amount'>[];
  }): Promise<{ message: string; success: boolean }> => {
    const res = await api.post<{ message: string; success: boolean }>('/api/profile/setup', payload);
    return res.data;
  },
};

// Debts Endpoints
export const debtsApi = {
  getDebts: async (): Promise<Debt[]> => {
    const res = await api.get<Debt[]>('/api/debts');
    return res.data;
  },

  createDebt: async (payload: Omit<Debt, 'id'>): Promise<Debt> => {
    const res = await api.post<Debt>('/api/debts', payload);
    return res.data;
  },
};

// Goals Endpoints
export const goalsApi = {
  getGoals: async (): Promise<Goal[]> => {
    const res = await api.get<Goal[]>('/api/goals');
    return res.data;
  },

  createGoal: async (payload: Omit<Goal, 'id' | 'current_amount'>): Promise<Goal> => {
    const res = await api.post<Goal>('/api/goals', payload);
    return res.data;
  },
};

// Transactions Endpoints
export const transactionsApi = {
  getTransactions: async (page = 1, limit = 20): Promise<{ transactions: Transaction[]; total: number; page: number }> => {
    const res = await api.get<{ transactions: Transaction[]; total: number; page: number }>(
      `/api/transactions?page=${page}&limit=${limit}`
    );
    return res.data;
  },

  createTransaction: async (payload: Omit<Transaction, 'id'>): Promise<Transaction> => {
    const res = await api.post<Transaction>('/api/transactions', payload);
    return res.data;
  },

  getTransactionSummary: async (): Promise<TransactionSummary> => {
    const res = await api.get<TransactionSummary>('/api/transactions/summary');
    return res.data;
  },
};

// AI Analysis & Chat Endpoints
export const aiApi = {
  analyze: async (payload?: { message?: string; analysis_type?: string }): Promise<AnalysisResult> => {
    const res = await api.post<AnalysisResult>('/api/analyze', payload || {});
    return res.data;
  },

  chat: async (payload: { message: string; session_id?: string }): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>('/api/chat', payload);
    return res.data;
  },
};
