import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger("finwise.calculators")


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


def format_currency(amount: Optional[float], currency_code: str = "INR") -> str:
    """Format currency amount with appropriate currency symbol (INR: ₹)."""
    if amount is None:
        return "-"

    val = float(amount)
    code = (currency_code or "INR").strip().upper()

    if code in ("INR", "RS", "RUPEES"):
        # Format as ₹12,34,567.00 (Indian numbering system) or standard comma formatted
        # Standard negative check
        prefix = "-" if val < 0 else ""
        abs_val = abs(val)

        # Indian numbering grouping
        cents = f"{abs_val:.2f}".split(".")[1]
        int_part = str(int(abs_val))

        if len(int_part) <= 3:
            formatted_int = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            # split into pairs from right
            pairs = []
            while remaining:
                pairs.append(remaining[-2:])
                remaining = remaining[:-2]
            pairs.reverse()
            formatted_int = ",".join(pairs) + "," + last_three

        return f"{prefix}₹{formatted_int}.{cents}"
    else:
        return f"{code} {val:,.2f}"


class FinancialCalculators:
    """Financial calculation utilities for loans, compounding, retirement, and risk."""

    @staticmethod
    def calculate_compound_interest(
        principal: float,
        rate: float,
        years: int,
        compounding: str = "annual",
    ) -> Dict[str, float]:
        """Calculate compound interest with different compounding frequencies."""
        compounding_factors = {
            "annual": 1,
            "semi-annual": 2,
            "quarterly": 4,
            "monthly": 12,
            "daily": 365,
        }
        n = compounding_factors.get(compounding.lower(), 1)
        rate_decimal = rate / 100.0
        amount = principal * ((1 + rate_decimal / n) ** (n * years))
        interest_earned = amount - principal

        return {
            "final_amount": round(amount, 2),
            "interest_earned": round(interest_earned, 2),
            "total_contributions": round(principal, 2),
        }

    @staticmethod
    def calculate_loan_payment(
        principal: float,
        annual_rate: float,
        years: int,
    ) -> Dict[str, float]:
        """Calculate monthly EMI/payment using amortization formula."""
        if years <= 0:
            return {"monthly_payment": principal, "total_interest": 0.0, "total_payment": principal}

        monthly_rate = (annual_rate / 100.0) / 12.0
        n_payments = years * 12

        if monthly_rate == 0:
            monthly_payment = principal / n_payments
        else:
            monthly_payment = (
                principal * (monthly_rate * (1 + monthly_rate) ** n_payments)
                / ((1 + monthly_rate) ** n_payments - 1)
            )

        total_payment = monthly_payment * n_payments
        total_interest = total_payment - principal

        return {
            "monthly_payment": round(monthly_payment, 2),
            "total_interest": round(total_interest, 2),
            "total_payment": round(total_payment, 2),
        }

    @staticmethod
    def calculate_debt_snowball(debts: List[Dict[str, Any]], extra_monthly: float = 100.0) -> List[Dict[str, Any]]:
        """Calculate debt snowball repayment plan (smallest balance first)."""
        if not debts:
            return []

        sorted_debts = [dict(d) for d in sorted(debts, key=lambda x: float(x.get("balance", 0)))]
        extra_payment = extra_monthly

        for index, debt in enumerate(sorted_debts):
            balance = float(debt.get("balance", 0))
            min_payment = float(debt.get("minimum_payment", max(50.0, balance * 0.03)))
            interest_rate = (float(debt.get("interest_rate", 0)) / 100.0) / 12.0

            months = 0
            while balance > 0 and months < 600:
                monthly_interest = balance * interest_rate
                total_pay = min_payment + extra_payment
                if total_pay > balance + monthly_interest:
                    total_pay = balance + monthly_interest

                balance = balance + monthly_interest - total_pay
                months += 1

            debt["payoff_months"] = months
            debt["payoff_order"] = index + 1
            if len(sorted_debts) > index + 1:
                extra_payment += min_payment

        return sorted_debts

    @staticmethod
    def calculate_retirement_savings(
        current_age: int,
        retirement_age: int,
        current_savings: float,
        monthly_contribution: float,
        expected_return: float,
    ) -> Dict[str, float]:
        """Project future retirement corpus given expected annual returns and contributions."""
        years_to_retirement = max(1, retirement_age - current_age)
        months_to_retirement = years_to_retirement * 12
        monthly_rate = (expected_return / 100.0) / 12.0

        if monthly_rate > 0:
            future_principal = current_savings * ((1 + monthly_rate) ** months_to_retirement)
            future_contributions = (
                monthly_contribution
                * (((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate)
            )
        else:
            future_principal = current_savings
            future_contributions = monthly_contribution * months_to_retirement

        projected = future_principal + future_contributions
        total_contributed = current_savings + (monthly_contribution * months_to_retirement)
        growth = projected - total_contributed

        return {
            "projected_savings": round(projected, 2),
            "total_contributions": round(total_contributed, 2),
            "growth_earned": round(growth, 2),
        }

    @staticmethod
    def assess_risk_profile(
        age: int,
        investment_experience: str,
        time_horizon: int,
        risk_tolerance: str,
    ) -> RiskProfile:
        """Score and classify investor risk profile based on financial demographics."""
        score = 0

        # Age scoring
        if age < 30:
            score += 3
        elif age < 50:
            score += 2
        else:
            score += 1

        # Investment experience scoring
        exp_map = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 3}
        score += exp_map.get(str(investment_experience).lower(), 1)

        # Time horizon scoring
        if time_horizon > 10:
            score += 3
        elif time_horizon >= 5:
            score += 2
        else:
            score += 1

        # Self-declared risk tolerance scoring
        tol_map = {"conservative": 0, "low": 0, "moderate": 1, "medium": 1, "aggressive": 2, "high": 2}
        score += tol_map.get(str(risk_tolerance).lower(), 1)

        if score >= 8:
            return RiskProfile.AGGRESSIVE
        elif score >= 5:
            return RiskProfile.MODERATE
        else:
            return RiskProfile.CONSERVATIVE


class DataProcessor:
    """Transaction categorization, trend analysis, anomaly detection, and ratio calculations."""

    @staticmethod
    def categorize_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize transactions into income, expenses, and investments."""
        categorized: Dict[str, List[Dict[str, Any]]] = {
            "income": [],
            "expenses": [],
            "investments": [],
            "transfers": [],
        }

        for txn in transactions:
            amt = float(txn.get("amount", 0.0))
            category = str(txn.get("category", "")).lower()
            desc = str(txn.get("description", "")).lower()
            txn_type = str(txn.get("type", "")).lower()

            if txn_type == "income" or (amt > 0 and txn_type != "expense"):
                categorized["income"].append(txn)
            elif "invest" in category or "stock" in category or "mutual" in desc or "sip" in desc:
                categorized["investments"].append(txn)
            elif "transfer" in category or "transfer" in desc:
                categorized["transfers"].append(txn)
            else:
                categorized["expenses"].append(txn)

        return categorized

    @staticmethod
    def analyze_spending_trends(transactions: List[Dict[str, Any]], period: str = "monthly") -> Dict[str, Any]:
        """Aggregate expenses by month or category into clean dict structures."""
        if not transactions:
            return {
                "trends": {},
                "summary": {"total_spending": 0.0, "average_monthly_spending": 0.0, "top_categories": {}},
            }

        try:
            df = pd.DataFrame(transactions)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

            # Look at expense transactions
            if "type" in df.columns:
                expenses_df = df[df["type"] == "expense"].copy()
            else:
                expenses_df = df[df["amount"] < 0].copy()

            expenses_df["amount"] = expenses_df["amount"].abs()
            total_spending = float(expenses_df["amount"].sum())

            top_cats_series = expenses_df.groupby("category")["amount"].sum().nlargest(5)
            top_categories = {str(k): round(float(v), 2) for k, v in top_cats_series.items()}

            trends = {}
            if "date" in expenses_df.columns:
                try:
                    expenses_df["date"] = pd.to_datetime(expenses_df["date"])
                    monthly = expenses_df.groupby(expenses_df["date"].dt.to_period("M"))["amount"].sum()
                    avg_spending = float(monthly.mean()) if len(monthly) > 0 else total_spending
                    for p, val in monthly.items():
                        trends[str(p)] = round(float(val), 2)
                except Exception:
                    avg_spending = total_spending
            else:
                avg_spending = total_spending

            return {
                "trends": trends,
                "summary": {
                    "total_spending": round(total_spending, 2),
                    "average_monthly_spending": round(avg_spending, 2),
                    "top_categories": top_categories,
                },
            }
        except Exception as exc:
            logger.error("Error analyzing spending trends: %s", exc)
            return {
                "trends": {},
                "summary": {"total_spending": 0.0, "average_monthly_spending": 0.0, "top_categories": {}},
            }

    @staticmethod
    def calculate_financial_ratios(
        income: float,
        expenses: float,
        debts: List[Dict[str, Any]],
        savings: float,
    ) -> Dict[str, float]:
        """Calculate key financial health metrics and ratios."""
        total_debt = sum(float(debt.get("balance", 0.0)) for debt in debts)
        monthly_debt_payments = sum(float(debt.get("minimum_payment", 0.0)) for debt in debts)

        savings_rate = ((income - expenses) / income * 100.0) if income > 0 else 0.0
        debt_to_income = (monthly_debt_payments / income * 100.0) if income > 0 else 0.0
        emergency_months = (savings / expenses) if expenses > 0 else 0.0

        return {
            "savings_rate": round(savings_rate, 2),
            "debt_to_income": round(debt_to_income, 2),
            "net_worth": round(savings - total_debt, 2),
            "emergency_fund_months": round(emergency_months, 2),
        }

    @staticmethod
    def detect_anomalies(transactions: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Identify statistical outliers in transaction amounts."""
        if len(transactions) < 5:
            return []

        try:
            amounts = [abs(float(t.get("amount", 0.0))) for t in transactions]
            series = pd.Series(amounts)
            mean = float(series.mean())
            std = float(series.std())

            if std == 0:
                return []

            anomalies = []
            for t in transactions:
                amt = abs(float(t.get("amount", 0.0)))
                z_score = (amt - mean) / std
                if z_score > threshold:
                    anomalies.append({
                        "description": str(t.get("description", "Unknown")),
                        "amount": amt,
                        "category": str(t.get("category", "General")),
                        "date": str(t.get("date", "")),
                        "z_score": round(z_score, 2),
                        "anomaly_type": "high_spending" if float(t.get("amount", 0.0)) < 0 or t.get("type") == "expense" else "high_income",
                    })

            return anomalies
        except Exception as exc:
            logger.error("Error detecting anomalies: %s", exc)
            return []
