"""
Specialist financial agents.
"""

from agents.budget_planner import BudgetPlannerAgent
from agents.debt_optimizer import DebtOptimizerAgent
from agents.financial_educator import FinancialEducatorAgent
from agents.income_analyzer import IncomeExpenseAnalyzerAgent
from agents.investment_advisor import InvestmentAdvisorAgent
from agents.master_agent import MasterFinancialStrategistAgent

__all__ = [
    "MasterFinancialStrategistAgent",
    "BudgetPlannerAgent",
    "DebtOptimizerAgent",
    "IncomeExpenseAnalyzerAgent",
    "InvestmentAdvisorAgent",
    "FinancialEducatorAgent",
]
