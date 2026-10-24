import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from tools.calculators import format_currency

logger = logging.getLogger("finwise.agents.debt_optimizer")


class DebtOptimizerAgent:
    """Optimizes debt repayment strategies via Avalanche and Snowball algorithms."""

    def optimize_repayment(self, debts: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized repayment schedule and comparison between Avalanche and Snowball methods."""
        logger.info("DebtOptimizerAgent optimizing %d debt items", len(debts))

        try:
            if not debts:
                return self._get_no_debt_response()

            debt_analysis = self._analyze_debt_situation(debts, user_profile)
            snowball_plan = self._calculate_snowball_method(debts, user_profile)
            avalanche_plan = self._calculate_avalanche_method(debts, user_profile)
            optimal_strategy = self._determine_optimal_strategy(snowball_plan, avalanche_plan, user_profile)
            consolidation = self._analyze_consolidation_options(debts, user_profile)
            recommendations = self._generate_debt_recommendations(
                debts, debt_analysis, optimal_strategy, consolidation, user_profile
            )

            return {
                "current_debt_situation": debt_analysis,
                "snowball_method": snowball_plan,
                "avalanche_method": avalanche_plan,
                "recommended_strategy": optimal_strategy,
                "consolidation_options": consolidation,
                "detailed_recommendations": recommendations,
            }
        except Exception as exc:
            logger.error("Error optimizing debt repayment: %s", exc)
            return {
                "error": str(exc),
                "detailed_recommendations": "Unable to calculate debt payoff plan.",
            }

    def _analyze_debt_situation(self, debts: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        total_debt = sum(float(d.get("balance", 0.0)) for d in debts)
        total_minimum = sum(float(d.get("minimum_payment", 0.0)) for d in debts)
        weighted_rate = (
            sum(float(d.get("balance", 0.0)) * float(d.get("interest_rate", 0.0)) for d in debts) / total_debt
            if total_debt > 0
            else 0.0
        )

        annual_income = float(user_profile.get("annual_income", 0.0))
        monthly_income = annual_income / 12.0
        debt_to_income = (total_minimum / monthly_income * 100.0) if monthly_income > 0 else 0.0

        return {
            "total_debt": round(total_debt, 2),
            "total_minimum_payments": round(total_minimum, 2),
            "weighted_interest_rate": round(weighted_rate, 2),
            "debt_to_income_ratio": round(debt_to_income, 2),
            "number_of_debts": len(debts),
            "high_interest_debts": len([d for d in debts if float(d.get("interest_rate", 0.0)) >= 12.0]),
        }

    def _calculate_extra_capacity(self, user_profile: Dict[str, Any]) -> float:
        annual = float(user_profile.get("annual_income", 0.0))
        monthly_income = annual / 12.0
        monthly_expenses = float(user_profile.get("monthly_expenses", 0.0))
        surplus = max(0.0, monthly_income - monthly_expenses)
        # Allocate up to 50% of free monthly surplus, minimum 500 INR
        return max(500.0, round(surplus * 0.5, 2))

    def _calculate_snowball_method(self, debts: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Snowball: Repay smallest balance first to build behavioral momentum."""
        sorted_debts = sorted(debts, key=lambda x: float(x.get("balance", 0.0)))
        extra_payment = self._calculate_extra_capacity(user_profile)

        payoff_plan = []
        total_interest = 0.0
        current_month = 0

        for index, debt in enumerate(sorted_debts):
            balance = float(debt.get("balance", 0.0))
            monthly_rate = (float(debt.get("interest_rate", 0.0)) / 100.0) / 12.0
            min_payment = float(debt.get("minimum_payment", max(50.0, balance * 0.03)))

            if index > 0:
                extra_payment += float(sorted_debts[index - 1].get("minimum_payment", 0.0))

            months = 0
            interest_paid = 0.0
            while balance > 0 and months < 600:
                interest = balance * monthly_rate
                payment = min_payment + extra_payment
                if payment > balance + interest:
                    payment = balance + interest

                interest_paid += interest
                balance = balance + interest - payment
                months += 1

            payoff_plan.append({
                "debt_name": debt.get("name", "Debt"),
                "initial_balance": float(debt.get("balance", 0.0)),
                "payoff_months": months,
                "total_interest": round(interest_paid, 2),
                "payoff_order": index + 1,
            })
            total_interest += interest_paid
            current_month += months

        return {
            "payoff_plan": payoff_plan,
            "total_payoff_time_months": current_month,
            "total_interest_paid": round(total_interest, 2),
            "completion_date": self._calculate_completion_date(current_month),
        }

    def _calculate_avalanche_method(self, debts: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Avalanche: Repay highest interest rate debt first to minimize total interest paid."""
        sorted_debts = sorted(debts, key=lambda x: float(x.get("interest_rate", 0.0)), reverse=True)
        extra_payment = self._calculate_extra_capacity(user_profile)

        active = [dict(d) for d in sorted_debts]
        total_interest = 0.0
        current_month = 0
        payoff_plan = []

        while active and current_month < 600:
            total_min = sum(float(d.get("minimum_payment", 0.0)) for d in active)
            available_pool = total_min + extra_payment

            focus = active[0]
            other_mins = sum(float(d.get("minimum_payment", 0.0)) for d in active[1:])
            focus_payment = available_pool - other_mins

            balance = float(focus.get("balance", 0.0))
            monthly_rate = (float(focus.get("interest_rate", 0.0)) / 100.0) / 12.0
            monthly_interest = balance * monthly_rate

            if focus_payment > balance + monthly_interest:
                focus_payment = balance + monthly_interest

            balance = balance + monthly_interest - focus_payment
            focus["balance"] = balance
            total_interest += monthly_interest

            if balance <= 0:
                initial_b = next((float(d.get("balance", 0.0)) for d in debts if d.get("name") == focus.get("name")), 0.0)
                payoff_plan.append({
                    "debt_name": focus.get("name"),
                    "initial_balance": initial_b,
                    "payoff_months": current_month + 1,
                    "payoff_order": len(payoff_plan) + 1,
                })
                active.pop(0)

            current_month += 1

        return {
            "payoff_plan": payoff_plan,
            "total_payoff_time_months": current_month,
            "total_interest_paid": round(total_interest, 2),
            "completion_date": self._calculate_completion_date(current_month),
        }

    def _determine_optimal_strategy(
        self,
        snowball: Dict[str, Any],
        avalanche: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        snow_interest = snowball.get("total_interest_paid", 0.0)
        ava_interest = avalanche.get("total_interest_paid", 0.0)
        snow_time = snowball.get("total_payoff_time_months", 0)
        ava_time = avalanche.get("total_payoff_time_months", 0)

        debts_count = len(user_profile.get("debts", []))
        risk_tol = str(user_profile.get("risk_tolerance", "moderate")).lower()
        currency = str(user_profile.get("currency") or "INR")

        if ava_interest <= snow_interest and ava_time <= snow_time:
            optimal = "avalanche"
            savings = round(snow_interest - ava_interest, 2)
            rationale = (
                f"Mathematically optimal: Avalanche saves approximately {format_currency(savings, currency)} "
                "in total interest costs by attacking high-rate balances first."
            )
        else:
            optimal = "snowball"
            savings = round(abs(snow_interest - ava_interest), 2)
            rationale = (
                "Snowball provides fastest psychological momentum through early loan elimination wins."
            )

        if debts_count >= 3 and risk_tol == "conservative" and savings < 5000:
            optimal = "snowball"
            rationale = "Snowball recommended for conservative risk profile to gain quick momentum and simplify accounts."

        return {
            "recommended_method": optimal,
            "interest_savings": savings,
            "time_savings_months": abs(snow_time - ava_time),
            "rationale": rationale,
        }

    def _analyze_consolidation_options(self, debts: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        total_debt = sum(float(d.get("balance", 0.0)) for d in debts)
        weighted_rate = (
            sum(float(d.get("balance", 0.0)) * float(d.get("interest_rate", 0.0)) for d in debts) / total_debt
            if total_debt > 0
            else 0.0
        )

        options = []
        if total_debt >= 50000 and weighted_rate >= 12.0:
            options.append({
                "type": "Personal Debt Consolidation Loan",
                "estimated_rate": 10.5,
                "potential_savings": round(total_debt * ((weighted_rate - 10.5) / 100.0), 2),
                "consideration": "Fixed monthly EMI simplifies multi-debt tracking and slashes interest burden.",
            })

        high_interest = [d for d in debts if float(d.get("interest_rate", 0.0)) >= 18.0]
        if high_interest:
            options.append({
                "type": "Balance Transfer / EMI Conversion",
                "estimated_rate": 12.0,
                "potential_savings": round(sum(float(d.get("balance", 0.0)) * (float(d.get("interest_rate", 0.0)) - 12.0) / 100.0 for d in high_interest), 2),
                "consideration": "Transfer expensive credit card revolving balances into structured low-interest EMIs.",
            })

        return {
            "options": options,
            "current_weighted_rate": round(weighted_rate, 2),
            "recommended": len(options) > 0 and weighted_rate > 12.0,
        }

    def _calculate_completion_date(self, months: int) -> str:
        future_dt = datetime.now() + timedelta(days=months * 30)
        return future_dt.strftime("%B %Y")

    def _get_no_debt_response(self) -> Dict[str, Any]:
        return {
            "current_debt_situation": {"total_debt": 0.0, "debt_to_income_ratio": 0.0, "number_of_debts": 0},
            "snowball_method": {"payoff_plan": [], "total_payoff_time_months": 0, "total_interest_paid": 0.0},
            "avalanche_method": {"payoff_plan": [], "total_payoff_time_months": 0, "total_interest_paid": 0.0},
            "recommended_strategy": {"recommended_method": "none", "rationale": "No outstanding debts to optimize. Allocate surplus to emergency savings and investing."},
            "consolidation_options": {"options": [], "recommended": False},
            "detailed_recommendations": "No active debts found. Your balance sheet has zero leverage. Focus on asset accumulation.",
        }

    def _generate_debt_recommendations(
        self,
        debts: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        strategy: Dict[str, Any],
        consolidation: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> str:
        currency = str(user_profile.get("currency") or "INR")
        method = strategy.get("recommended_method", "avalanche").upper()
        interest_savings = strategy.get("interest_savings", 0.0)

        sorted_debts = sorted(debts, key=lambda d: float(d.get("interest_rate", 0.0)), reverse=True)
        inventory_lines = [
            f"- **{d.get('name')}**: Balance {format_currency(float(d.get('balance', 0.0)), currency)} at {d.get('interest_rate')}% APR (Min payment: {format_currency(float(d.get('minimum_payment', 0.0)), currency)})"
            for d in sorted_debts
        ]

        consolidation_lines = [
            f"- **{opt.get('type')}**: Est. APR {opt.get('estimated_rate')}%, potential savings: {format_currency(opt.get('potential_savings'), currency)}. *{opt.get('consideration')}*"
            for opt in consolidation.get("options", [])
        ] or ["- Debt consolidation is not currently required."]

        first_target = sorted_debts[0].get("name") if sorted_debts else "Priority debt"

        return "\n".join([
            "### Debt Repayment Optimization Blueprint",
            "",
            f"- **Total Outstanding Debt:** {format_currency(analysis.get('total_debt', 0.0), currency)}",
            f"- **Debt-to-Income Ratio:** {analysis.get('debt_to_income_ratio', 0.0)}%",
            f"- **Weighted Average Interest Rate:** {analysis.get('weighted_interest_rate', 0.0)}%",
            f"- **Optimal Strategy:** {method} Method",
            f"- **Projected Interest Savings:** {format_currency(interest_savings, currency)}",
            "",
            "#### Debt Portfolio Inventory",
            *inventory_lines,
            "",
            "#### Execution Strategy",
            f"1. Schedule automatic minimum payments on every debt account to maintain flawless credit standing.",
            f"2. Concentrate all discretionary surplus onto **{first_target}** until it reaches zero balance.",
            f"3. Once cleared, roll that entire monthly payment power into the next targeted account.",
            "",
            "#### Consolidation & Refinancing Review",
            *consolidation_lines,
        ])
