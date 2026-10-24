import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, List
from langgraph.graph import END, StateGraph

from graph.state import AgentState, AnalysisType
from agents.budget_planner import BudgetPlannerAgent
from agents.debt_optimizer import DebtOptimizerAgent
from agents.financial_educator import FinancialEducatorAgent
from agents.income_analyzer import IncomeExpenseAnalyzerAgent
from agents.investment_advisor import InvestmentAdvisorAgent
from agents.master_agent import MasterFinancialStrategistAgent

logger = logging.getLogger("finwise.graph.workflow")


class FinancialWorkflow:
    """Orchestrates the multi-agent personal finance state graph."""

    def __init__(self):
        self.master_agent = MasterFinancialStrategistAgent()
        self.income_analyzer = IncomeExpenseAnalyzerAgent()
        self.budget_planner = BudgetPlannerAgent()
        self.investment_advisor = InvestmentAdvisorAgent()
        self.debt_optimizer = DebtOptimizerAgent()
        self.financial_educator = FinancialEducatorAgent()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        workflow = StateGraph(AgentState)

        # Register nodes
        workflow.add_node("master_agent", self._master_agent_node)
        workflow.add_node("income_analyzer", self._income_analyzer_node)
        workflow.add_node("budget_planner", self._budget_planner_node)
        workflow.add_node("investment_advisor", self._investment_advisor_node)
        workflow.add_node("debt_optimizer", self._debt_optimizer_node)
        workflow.add_node("financial_educator", self._financial_educator_node)
        workflow.add_node("comprehensive_analysis", self._comprehensive_analysis_node)
        workflow.add_node("synthesize", self._synthesize_node)

        # Workflow entry & routing
        workflow.set_entry_point("master_agent")
        workflow.add_conditional_edges(
            "master_agent",
            self._route_based_on_analysis,
            {
                AnalysisType.INCOME_EXPENSE.value: "income_analyzer",
                AnalysisType.BUDGET_PLANNING.value: "budget_planner",
                AnalysisType.INVESTMENT_ADVICE.value: "investment_advisor",
                AnalysisType.DEBT_OPTIMIZATION.value: "debt_optimizer",
                AnalysisType.FINANCIAL_EDUCATION.value: "financial_educator",
                AnalysisType.COMPREHENSIVE.value: "comprehensive_analysis",
                "end": END,
            },
        )

        # Edges to final synthesis or END
        workflow.add_edge("income_analyzer", "synthesize")
        workflow.add_edge("budget_planner", "synthesize")
        workflow.add_edge("investment_advisor", "synthesize")
        workflow.add_edge("debt_optimizer", "synthesize")
        workflow.add_edge("comprehensive_analysis", "synthesize")
        workflow.add_edge("financial_educator", END)
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _execute_with_trace(
        self,
        state: AgentState,
        agent_name: str,
        handler: Callable[[], Dict[str, Any]],
    ) -> Dict[str, Any]:
        trace = list(state.get("workflow_trace") or [])
        started_at = self._utc_now_iso()

        try:
            updates = handler() or {}
            ended_at = self._utc_now_iso()
            status = "error" if updates.get("error") else "success"
            trace.append({
                "agent": agent_name,
                "startedAt": started_at,
                "endedAt": ended_at,
                "status": status,
                **({"error": updates.get("error")} if updates.get("error") else {}),
            })
            updates["workflow_trace"] = trace
            return updates
        except Exception as exc:
            ended_at = self._utc_now_iso()
            trace.append({
                "agent": agent_name,
                "startedAt": started_at,
                "endedAt": ended_at,
                "status": "error",
                "error": str(exc),
            })
            logger.exception("%s node execution failed", agent_name)
            raise

    def _route_based_on_analysis(self, state: AgentState) -> str:
        analysis_val = str(state.get("current_analysis", {}).get("type") or AnalysisType.COMPREHENSIVE.value).lower()
        if not state.get("user_profile") and analysis_val == AnalysisType.COMPREHENSIVE.value:
            return AnalysisType.FINANCIAL_EDUCATION.value
        return analysis_val

    def _master_agent_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            # If explicit analysis_type was already passed in state options, honor it
            explicit_type = state.get("options", {}).get("analysis_type")
            if explicit_type and explicit_type in [t.value for t in AnalysisType]:
                analysis_val = explicit_type
            else:
                user_input = state.get("user_input", "")
                user_profile = state.get("user_profile")
                history = state.get("conversation_history") or []
                summary = state.get("session_summary")

                atype = self.master_agent.determine_analysis_type(
                    user_input=user_input,
                    user_profile=user_profile,
                    conversation_history=history,
                    session_summary=summary,
                )
                analysis_val = atype.value if hasattr(atype, "value") else str(atype)

            return {
                "current_analysis": {"type": analysis_val},
                "next_agent": analysis_val,
            }

        return self._execute_with_trace(state, "master_agent", _run)

    def _income_analyzer_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            profile = state.get("user_profile") or {}
            txns = profile.get("transactions", [])
            return {
                "income_analysis": self.income_analyzer.analyze_finances(txns),
                "next_agent": "synthesize",
            }

        return self._execute_with_trace(state, "income_analyzer", _run)

    def _budget_planner_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            profile = state.get("user_profile") or {}
            return {
                "budget_plan": self.budget_planner.create_budget_plan(profile),
                "next_agent": "synthesize",
            }

        return self._execute_with_trace(state, "budget_planner", _run)

    def _investment_advisor_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            profile = state.get("user_profile") or {}
            return {
                "investment_advice": self.investment_advisor.provide_advice(profile),
                "next_agent": "synthesize",
            }

        return self._execute_with_trace(state, "investment_advisor", _run)

    def _debt_optimizer_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            profile = state.get("user_profile") or {}
            debts = profile.get("debts", [])
            return {
                "debt_optimization": self.debt_optimizer.optimize_repayment(debts, profile),
                "next_agent": "synthesize",
            }

        return self._execute_with_trace(state, "debt_optimizer", _run)

    def _financial_educator_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            user_input = state.get("user_input", "")
            profile = state.get("user_profile")
            result = self.financial_educator.explain_concept(user_input, profile)
            output = result.get("explanation", "")
            return {
                "financial_education": result,
                "final_output": output,
                "fallback_used": bool(result.get("fallback_used")),
            }

        return self._execute_with_trace(state, "financial_educator", _run)

    def _comprehensive_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        trace = list(state.get("workflow_trace") or [])
        profile = state.get("user_profile") or {}

        # 1. Income Analysis
        t_start = self._utc_now_iso()
        income_res = self.income_analyzer.analyze_finances(profile.get("transactions", []))
        trace.append({"agent": "income_analyzer", "startedAt": t_start, "endedAt": self._utc_now_iso(), "status": "success"})

        # 2. Budget Planner
        t_start = self._utc_now_iso()
        budget_res = self.budget_planner.create_budget_plan(profile)
        trace.append({"agent": "budget_planner", "startedAt": t_start, "endedAt": self._utc_now_iso(), "status": "success"})

        # 3. Investment Advisor
        t_start = self._utc_now_iso()
        invest_res = self.investment_advisor.provide_advice(profile)
        trace.append({"agent": "investment_advisor", "startedAt": t_start, "endedAt": self._utc_now_iso(), "status": "success"})

        # 4. Debt Optimizer
        t_start = self._utc_now_iso()
        debt_res = self.debt_optimizer.optimize_repayment(profile.get("debts", []), profile)
        trace.append({"agent": "debt_optimizer", "startedAt": t_start, "endedAt": self._utc_now_iso(), "status": "success"})

        return {
            "income_analysis": income_res,
            "budget_plan": budget_res,
            "investment_advice": invest_res,
            "debt_optimization": debt_res,
            "workflow_trace": trace,
            "next_agent": "synthesize",
        }

    def _synthesize_node(self, state: AgentState) -> Dict[str, Any]:
        def _run():
            profile = state.get("user_profile")
            analyses = {
                "income_analysis": state.get("income_analysis"),
                "budget_plan": state.get("budget_plan"),
                "investment_advice": state.get("investment_advice"),
                "debt_optimization": state.get("debt_optimization"),
            }
            context = {
                "conversation_history": state.get("conversation_history") or [],
                "session_summary": state.get("session_summary"),
                "options": state.get("options") or {},
            }
            final_plan = self.master_agent.synthesize_plan(profile, analyses, context=context)
            return {
                "final_output": final_plan,
                "next_agent": "end",
                "fallback_used": bool(final_plan.get("fallback_used")),
            }

        return self._execute_with_trace(state, "master_synthesis", _run)

    def process_request(
        self,
        user_input: str,
        user_profile: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_summary: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Invoke the graph with a populated initial AgentState."""
        initial_state: AgentState = {
            "user_input": user_input,
            "user_profile": user_profile,
            "conversation_history": conversation_history or [],
            "session_summary": session_summary,
            "options": options or {},
            "current_analysis": {},
            "income_analysis": None,
            "budget_plan": None,
            "investment_advice": None,
            "debt_optimization": None,
            "financial_education": None,
            "next_agent": "master_agent",
            "final_output": None,
            "fallback_used": False,
            "workflow_trace": [],
            "error": None,
        }

        try:
            return self.workflow.invoke(initial_state)
        except Exception as exc:
            logger.error("StateGraph workflow invocation failed: %s", exc)
            return {
                "final_output": {
                    "response": f"Encountered an issue running financial analysis: {exc}",
                    "agent": "master",
                    "plan": {},
                    "insights": [],
                },
                "fallback_used": True,
                "workflow_trace": initial_state.get("workflow_trace", []),
                "error": str(exc),
            }


def create_financial_workflow() -> FinancialWorkflow:
    return FinancialWorkflow()
