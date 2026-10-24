from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class AnalysisType(str, Enum):
    """Supported financial analysis modes."""
    INCOME_EXPENSE = "income_expense"
    BUDGET_PLANNING = "budget_planning"
    INVESTMENT_ADVICE = "investment_advice"
    DEBT_OPTIMIZATION = "debt_optimization"
    FINANCIAL_EDUCATION = "financial_education"
    COMPREHENSIVE = "comprehensive"


class AgentState(TypedDict):
    """LangGraph shared workflow state across financial specialist agents."""
    user_input: str
    user_profile: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, str]]
    session_summary: Optional[str]
    options: Dict[str, Any]
    current_analysis: Dict[str, Any]
    income_analysis: Optional[Dict[str, Any]]
    budget_plan: Optional[Dict[str, Any]]
    investment_advice: Optional[Dict[str, Any]]
    debt_optimization: Optional[Dict[str, Any]]
    financial_education: Optional[Dict[str, Any]]
    next_agent: str
    final_output: Optional[Any]
    fallback_used: bool
    workflow_trace: List[Dict[str, Any]]
    error: Optional[str]
