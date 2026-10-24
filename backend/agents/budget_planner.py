import logging
from typing import Any, Dict, List
from config import settings
from tools.calculators import format_currency

logger = logging.getLogger("finwise.agents.budget_planner")


class BudgetPlannerAgent:
    """Specialist agent that formulates and optimizes personalized monthly budget allocations."""

    def create_budget_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive budget plan based on income, expenses, debts, and goals."""
        logger.info("BudgetPlannerAgent generating budget plan")

        try:
            annual_income = float(user_profile.get("annual_income", 0.0))
            monthly_income = annual_income / 12.0
            expenses = float(user_profile.get("monthly_expenses", 0.0))
            savings = float(user_profile.get("savings", 0.0))
            goals = user_profile.get("financial_goals", []) or []
            debts = user_profile.get("debts", []) or []
            currency = str(user_profile.get("currency") or "INR")

            allocation = self._calculate_budget_allocation(monthly_income, expenses, goals, debts)
            savings_plan = self._create_savings_plan(monthly_income, expenses, goals, savings)
            debt_repayment = self._calculate_debt_repayment_budget(debts, monthly_income)
            detailed_recommendations = self._generate_detailed_budget(
                monthly_income, expenses, allocation, savings_plan, debt_repayment, goals, currency
            )

            emergency_fund_target = expenses * settings.EMERGENCY_FUND_MONTHS
            savings_rate = ((monthly_income - expenses) / monthly_income * 100.0) if monthly_income > 0 else 0.0

            return {
                "monthly_income": round(monthly_income, 2),
                "current_expenses": round(expenses, 2),
                "budget_allocation": allocation,
                "savings_plan": savings_plan,
                "debt_repayment_allocation": debt_repayment,
                "detailed_recommendations": detailed_recommendations,
                "emergency_fund_target": round(emergency_fund_target, 2),
                "savings_rate": round(savings_rate, 1),
            }
        except Exception as exc:
            logger.error("Error creating budget plan: %s", exc)
            return {
                "error": str(exc),
                "detailed_recommendations": "Unable to calculate budget plan due to missing or invalid profile data.",
            }

    def _calculate_budget_allocation(
        self,
        income: float,
        _expenses: float,
        goals: List[Dict[str, Any]],
        debts: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        total_debt_payments = sum(float(d.get("minimum_payment", 0.0)) for d in debts)
        goal_savings_needed = self._calculate_goal_savings(goals, income)

        debt_ratio = (total_debt_payments / income) if income > 0 else 0.0

        # When debt minimum payments are significant (>15% of income), apply aggressive debt-payoff split
        if debt_ratio > 0.15:
            return {
                "essential_expenses": round(income * 0.50, 2),
                "debt_repayment": round(max(total_debt_payments, income * 0.30), 2),
                "savings": round(income * 0.10, 2),
                "discretionary": round(income * 0.10, 2),
            }

        # Balanced allocation
        return {
            "housing": round(income * 0.25, 2),
            "transportation": round(income * 0.10, 2),
            "food_and_groceries": round(income * 0.12, 2),
            "healthcare": round(income * 0.08, 2),
            "debt_repayment": round(total_debt_payments, 2),
            "savings_and_investing": round(max(income * settings.DEFAULT_SAVINGS_RATE, goal_savings_needed), 2),
            "discretionary": round(income * 0.15, 2),
            "utilities_and_bills": round(income * 0.05, 2),
            "insurance": round(income * 0.05, 2),
        }

    def _calculate_goal_savings(self, goals: List[Dict[str, Any]], income: float) -> float:
        if not goals:
            return income * settings.DEFAULT_SAVINGS_RATE

        total_monthly = 0.0
        for goal in goals:
            target = float(goal.get("target_amount") or goal.get("target") or 0.0)
            timeline = int(goal.get("timeline_months", 12))
            current = float(goal.get("current_amount", 0.0))
            net_needed = max(0.0, target - current)
            total_monthly += (net_needed / timeline) if timeline > 0 else 0.0

        return min(total_monthly, income * 0.35)

    def _create_savings_plan(
        self,
        income: float,
        expenses: float,
        goals: List[Dict[str, Any]],
        current_savings: float,
    ) -> Dict[str, Any]:
        emergency_fund_target = expenses * settings.EMERGENCY_FUND_MONTHS
        emergency_fund_gap = max(0.0, emergency_fund_target - current_savings)

        goal_savings: Dict[str, Dict[str, Any]] = {}
        for goal in goals:
            name = str(goal.get("name", "Goal"))
            target = float(goal.get("target_amount") or goal.get("target") or 0.0)
            current = float(goal.get("current_amount", 0.0))
            timeline = int(goal.get("timeline_months", 12))
            net_needed = max(0.0, target - current)
            monthly = (net_needed / timeline) if timeline > 0 else 0.0

            goal_savings[name] = {
                "monthly_savings": round(monthly, 2),
                "target": round(target, 2),
                "current": round(current, 2),
                "timeline_months": timeline,
                "priority": goal.get("priority", 3),
            }

        total_monthly_goal_savings = sum(g["monthly_savings"] for g in goal_savings.values())

        return {
            "emergency_fund": {
                "target": round(emergency_fund_target, 2),
                "current": round(current_savings, 2),
                "gap": round(emergency_fund_gap, 2),
                "monthly_savings_needed": round(emergency_fund_gap / 6, 2) if emergency_fund_gap > 0 else 0.0,
            },
            "goal_savings": goal_savings,
            "total_monthly_savings": round(total_monthly_goal_savings, 2),
            "baseline_savings_target": round(income * settings.DEFAULT_SAVINGS_RATE, 2),
        }

    def _calculate_debt_repayment_budget(self, debts: List[Dict[str, Any]], income: float) -> Dict[str, Any]:
        if not debts:
            return {"total_monthly_payment": 0.0, "debts": []}

        total_min_payments = sum(float(d.get("minimum_payment", 0.0)) for d in debts)
        recommended_extra = round(min(income * 0.10, 5000.0 if income > 20000 else 500.0), 2)

        debt_details = []
        for d in debts:
            debt_details.append({
                "name": d.get("name", "Debt"),
                "balance": float(d.get("balance", 0.0)),
                "interest_rate": float(d.get("interest_rate", 0.0)),
                "minimum_payment": float(d.get("minimum_payment", 0.0)),
                "recommended_extra": round(recommended_extra / max(1, len(debts)), 2),
            })

        return {
            "total_monthly_payment": round(total_min_payments + recommended_extra, 2),
            "minimum_payments": round(total_min_payments, 2),
            "recommended_extra": recommended_extra,
            "debts": debt_details,
        }

    def _generate_detailed_budget(
        self,
        income: float,
        expenses: float,
        allocation: Dict[str, float],
        savings_plan: Dict[str, Any],
        debt_repayment: Dict[str, Any],
        goals: List[Dict[str, Any]],
        currency: str,
    ) -> str:
        """Deterministic budget recommendation markdown generation."""
        free_cash_flow = income - expenses
        allocation_lines = [
            f"- **{cat.replace('_', ' ').capitalize()}**: {format_currency(amt, currency)} ({(amt / income * 100):.1f}%)"
            for cat, amt in allocation.items()
            if income > 0
        ]

        emergency_fund = savings_plan.get("emergency_fund", {})
        debt_total = debt_repayment.get("total_monthly_payment", 0.0)

        top_goals = sorted(goals, key=lambda g: int(g.get("priority", 3)))[:3]
        goal_lines = [
            f"- {g.get('name')}: {format_currency(float(g.get('target_amount') or g.get('target') or 0.0), currency)} in {g.get('timeline_months', 12)} months"
            for g in top_goals
        ] or ["- Start by establishing an emergency fund before setting discretionary goals."]

        action_steps = [
            "1. Automate monthly savings transfers on your income disbursement date.",
            "2. Enforce category spending limits for discretionary purchases.",
            "3. Conduct weekly expense check-ins to prevent budget drift.",
        ]
        if free_cash_flow < 0:
            action_steps.insert(0, "0. Immediate adjustment: Reduce discretionary spending to close the monthly deficit.")

        return "\n".join([
            "### Recommended Budget Architecture",
            "",
            f"- **Monthly Net Income:** {format_currency(income, currency)}",
            f"- **Current Monthly Expenses:** {format_currency(expenses, currency)}",
            f"- **Free Monthly Cash Flow:** {format_currency(free_cash_flow, currency)}",
            "",
            "#### Monthly Allocation Breakdown",
            *allocation_lines,
            "",
            "#### Savings & Emergency Buffer",
            f"- **Emergency Target ({settings.EMERGENCY_FUND_MONTHS} Months):** {format_currency(emergency_fund.get('target', 0.0), currency)}",
            f"- **Current Reserves:** {format_currency(emergency_fund.get('current', 0.0), currency)}",
            f"- **Reserve Gap:** {format_currency(emergency_fund.get('gap', 0.0), currency)}",
            "",
            "#### Debt Servicing",
            f"- **Recommended Total Monthly Debt Payment:** {format_currency(debt_total, currency)}",
            "",
            "#### Key Financial Goals",
            *goal_lines,
            "",
            "#### Action Items",
            *action_steps,
        ])
