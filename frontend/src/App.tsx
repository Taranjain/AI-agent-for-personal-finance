import React from 'react';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Loader2 } from 'lucide-react';

const MainApp: React.FC = () => {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
        <p className="text-xs text-slate-500 font-medium tracking-wide">
          Initializing FinWise Engine...
        </p>
      </div>
    );
  }

  return token ? <Dashboard /> : <Login />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
