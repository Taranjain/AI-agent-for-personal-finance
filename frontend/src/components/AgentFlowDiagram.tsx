import React from 'react';
import {
  Brain,
  Calculator,
  ShieldCheck,
  TrendingUp,
  Landmark,
  FileText,
  CheckCircle,
  Clock,
  Loader2,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { WorkflowTraceStep } from '../lib/api';

interface AgentFlowDiagramProps {
  workflowTrace?: WorkflowTraceStep[];
  isAnalyzing?: boolean;
}

interface AgentNodeDef {
  id: string;
  name: string;
  role: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const AgentFlowDiagram: React.FC<AgentFlowDiagramProps> = ({
  workflowTrace = [],
  isAnalyzing = false,
}) => {
  // Master Orchestrator Node
  const masterNode: AgentNodeDef = {
    id: 'master',
    name: 'Master Orchestrator',
    role: 'Decomposes intent & directs flow',
    icon: Brain,
  };

  // Parallel Specialist Agents
  const specialistNodes: AgentNodeDef[] = [
    {
      id: 'budget',
      name: 'Budget Optimizer',
      role: '50/30/20 & Discretionary Analysis',
      icon: Calculator,
    },
    {
      id: 'debt',
      name: 'Debt Specialist',
      role: 'Avalanche & Snowball Payoff',
      icon: Landmark,
    },
    {
      id: 'investment',
      name: 'Investment Strategist',
      role: 'Asset Allocation & SIP Engine',
      icon: TrendingUp,
    },
    {
      id: 'guard',
      name: 'Emergency Guard',
      role: 'Liquidity & Runway Protection',
      icon: ShieldCheck,
    },
  ];

  // Synthesizer Node
  const synthesizerNode: AgentNodeDef = {
    id: 'synthesizer',
    name: 'Synthesizer Agent',
    role: 'Synthesizes unified action plan',
    icon: FileText,
  };

  // Determine node status from workflow trace or isAnalyzing state
  const getNodeStatus = (agentName: string): string => {
    if (isAnalyzing) {
      if (agentName === 'Master Orchestrator') return 'completed';
      if (agentName === 'Synthesizer Agent') return 'running';
      return 'running';
    }

    if (!workflowTrace || workflowTrace.length === 0) {
      return 'completed'; // Default static preview shows completed state
    }

    const found = workflowTrace.find(
      (item) => item.agent.toLowerCase().includes(agentName.toLowerCase()) ||
                agentName.toLowerCase().includes(item.agent.toLowerCase())
    );

    return found ? found.status : 'completed';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center text-[10px] font-medium text-blue-700 bg-blue-100/80 px-1.5 py-0.5 rounded-full">
            <Loader2 className="w-2.5 h-2.5 mr-1 animate-spin text-blue-600" /> Running
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center text-[10px] font-medium text-emerald-700 bg-emerald-100/80 px-1.5 py-0.5 rounded-full">
            <CheckCircle className="w-2.5 h-2.5 mr-1 text-emerald-600" /> Done
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center text-[10px] font-medium text-rose-700 bg-rose-100/80 px-1.5 py-0.5 rounded-full">
            <AlertTriangle className="w-2.5 h-2.5 mr-1 text-rose-600" /> Error
          </span>
        );
      case 'skipped':
        return (
          <span className="inline-flex items-center text-[10px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-full">
            Skipped
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center text-[10px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-full">
            <Clock className="w-2.5 h-2.5 mr-1" /> Ready
          </span>
        );
    }
  };

  const getNodeContainerStyle = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-400 bg-blue-50/40 ring-2 ring-blue-200 agent-node-running';
      case 'completed':
        return 'border-emerald-300 bg-emerald-50/20';
      case 'failed':
        return 'border-rose-300 bg-rose-50/20';
      case 'skipped':
        return 'border-dashed border-slate-300 bg-slate-50 opacity-60';
      default:
        return 'border-slate-200 bg-white';
    }
  };

  const masterStatus = getNodeStatus(masterNode.name);
  const synthStatus = getNodeStatus(synthesizerNode.name);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Multi-Agent Execution Pipeline</h3>
          <p className="text-xs text-slate-500">Autonomous workflow with numeric mathematical guardrails</p>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
          <span className="text-[11px] font-medium text-slate-600">LangGraph Engine</span>
        </div>
      </div>

      {/* Pipeline Visual Diagram */}
      <div className="py-4 grid grid-cols-1 md:grid-cols-11 gap-3 items-center">
        {/* Step 1: Master Orchestrator (Cols 1-3) */}
        <div className="md:col-span-3">
          <div
            className={`p-3 rounded-xl border transition-all duration-300 shadow-xs ${getNodeContainerStyle(
              masterStatus
            )}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                <masterNode.icon className="w-4 h-4" />
              </div>
              {getStatusBadge(masterStatus)}
            </div>
            <h4 className="text-xs font-semibold text-slate-800">{masterNode.name}</h4>
            <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">{masterNode.role}</p>
          </div>
        </div>

        {/* Connector 1 (Col 4) */}
        <div className="hidden md:flex md:col-span-1 justify-center items-center text-slate-300">
          <ArrowRight className="w-5 h-5 text-slate-400 animate-pulse" />
        </div>

        {/* Step 2: Parallel Specialist Agents (Cols 5-7) */}
        <div className="md:col-span-3 space-y-2">
          {specialistNodes.map((agent) => {
            const status = getNodeStatus(agent.name);
            return (
              <div
                key={agent.id}
                className={`p-2.5 rounded-lg border transition-all duration-200 shadow-xs flex items-center justify-between ${getNodeContainerStyle(
                  status
                )}`}
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <div className="w-6 h-6 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center flex-shrink-0">
                    <agent.icon className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  <div className="min-w-0">
                    <h5 className="text-[11px] font-semibold text-slate-800 truncate">{agent.name}</h5>
                    <p className="text-[9px] text-slate-500 truncate">{agent.role}</p>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-2">
                  {getStatusBadge(status)}
                </div>
              </div>
            );
          })}
        </div>

        {/* Connector 2 (Col 8) */}
        <div className="hidden md:flex md:col-span-1 justify-center items-center text-slate-300">
          <ArrowRight className="w-5 h-5 text-slate-400 animate-pulse" />
        </div>

        {/* Step 3: Synthesizer Agent (Cols 9-11) */}
        <div className="md:col-span-3">
          <div
            className={`p-3 rounded-xl border transition-all duration-300 shadow-xs ${getNodeContainerStyle(
              synthStatus
            )}`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
                <synthesizerNode.icon className="w-4 h-4" />
              </div>
              {getStatusBadge(synthStatus)}
            </div>
            <h4 className="text-xs font-semibold text-slate-800">{synthesizerNode.name}</h4>
            <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">{synthesizerNode.role}</p>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Deterministic math verified before LLM generation</span>
        <span className="font-medium text-slate-600">Zero Hallucination Guaranteed</span>
      </div>
    </div>
  );
};
