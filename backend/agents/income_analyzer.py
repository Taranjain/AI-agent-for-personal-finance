import logging
from typing import Any, Dict, List
from dateutil.parser import parse as parse_date
from tools.calculators import DataProcessor, FinancialCalculators, format_currency

logger = logging.getLogger("finwise.agents.income_analyzer")


class IncomeExpenseAnalyzerAgent:
    """Specialist agent for transaction analysis, cash flow trends, and spending patterns."""

    def __init__(self):
        self.data_processor = DataProcessor()
        self.calculators = FinancialCalculators()

    def analyze_finances(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive analysis of income, expenses, and cash flow health."""
        logger.info("IncomeExpenseAnalyzerAgent processing %d transactions", len(transactions or []))

        try:
            if not transactions:
                return self._get_empty_analysis()

            categorized = self._process_transactions(transactions)
            metrics = self._calculate_financial_metrics(categorized)
            patterns = self._detect_financial_patterns(categorized, metrics)
            insights = self._generate_comprehensive_insights(categorized, metrics, patterns)

            return {
                "categorized_data": categorized,
                "financial_metrics": metrics,
                "patterns_detected": patterns,
                "insights": insights,
                "summary_metrics": {
                    "net_cash_flow": metrics.get("net_cash_flow", 0.0),
                    "savings_rate": metrics.get("savings_rate", 0.0),
                    "total_income": metrics.get("total_income", 0.0),
                    "total_expenses": metrics.get("total_expenses", 0.0),
                },
                "health_score": self._calculate_financial_health_score(metrics),
            }
        except Exception as exc:
            logger.error("Error analyzing income and expenses: %s", exc)
            return {
                "error": str(exc),
                "summary_metrics": {"net_cash_flow": 0.0, "savings_rate": 0.0},
                "insights": "Unable to complete transaction analysis due to data processing error.",
            }

    def _process_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        categorized = self.data_processor.categorize_transactions(transactions)
        trends = self.data_processor.analyze_spending_trends(transactions, "monthly")
        anomalies = self.data_processor.detect_anomalies(transactions)
        category_breakdown = self._analyze_category_percentages(categorized)
        recurring = self._identify_recurring(transactions)

        return {
            "categorized_transactions": categorized,
            "spending_trends": trends,
            "anomalies": anomalies,
            "category_analysis": category_breakdown,
            "recurring_transactions": recurring,
        }

    def _analyze_category_percentages(self, categorized: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        expenses = categorized.get("expenses", [])
        total_exp = sum(abs(float(t.get("amount", 0.0))) for t in expenses)
        if total_exp == 0:
            return {}

        cat_totals: Dict[str, float] = {}
        for t in expenses:
            cat = str(t.get("category", "General")).title()
            cat_totals[cat] = cat_totals.get(cat, 0.0) + abs(float(t.get("amount", 0.0)))

        return {cat: round((amt / total_exp) * 100.0, 1) for cat, amt in cat_totals.items()}

    def _identify_recurring(self, transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        recurring: Dict[str, List[Dict[str, Any]]] = {"income": [], "expenses": []}
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for t in transactions:
            key = f"{str(t.get('description', '')).lower()}_{abs(float(t.get('amount', 0.0))):.0f}"
            groups.setdefault(key, []).append(t)

        for key, group in groups.items():
            if len(group) >= 2 or any(bool(t.get("is_recurring")) for t in group):
                first = group[0]
                t_type = "income" if float(first.get("amount", 0.0)) > 0 or first.get("type") == "income" else "expenses"
                recurring[t_type].append({
                    "description": first.get("description", "Recurring item"),
                    "amount": abs(float(first.get("amount", 0.0))),
                    "occurrences": len(group),
                })

        return recurring

    def _calculate_financial_metrics(self, categorized_data: Dict[str, Any]) -> Dict[str, float]:
        cats = categorized_data.get("categorized_transactions", {})
        total_income = sum(float(t.get("amount", 0.0)) for t in cats.get("income", []))
        total_expenses = sum(abs(float(t.get("amount", 0.0))) for t in cats.get("expenses", []))
        net_cash_flow = total_income - total_expenses
        savings_rate = ((net_cash_flow / total_income) * 100.0) if total_income > 0 else 0.0

        recurring_exp = categorized_data.get("recurring_transactions", {}).get("expenses", [])
        fixed_expenses = sum(float(e.get("amount", 0.0)) for e in recurring_exp)
        discretionary = max(0.0, total_expenses - fixed_expenses)

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "savings_rate": round(savings_rate, 1),
            "fixed_expenses": round(fixed_expenses, 2),
            "discretionary_expenses": round(discretionary, 2),
            "fixed_expense_ratio": round((fixed_expenses / total_income * 100.0), 1) if total_income > 0 else 0.0,
            "discretionary_ratio": round((discretionary / total_income * 100.0), 1) if total_income > 0 else 0.0,
        }

    def _detect_financial_patterns(self, categorized_data: Dict[str, Any], metrics: Dict[str, float]) -> Dict[str, Any]:
        patterns: Dict[str, List[str]] = {"strengths": [], "concerns": [], "opportunities": []}

        savings_rate = metrics.get("savings_rate", 0.0)
        net_flow = metrics.get("net_cash_flow", 0.0)

        if savings_rate >= 20.0:
            patterns["strengths"].append(f"Strong savings rate ({savings_rate:.1f}%), exceeding the 20% benchmark.")
        elif savings_rate > 0.0:
            patterns["opportunities"].append(f"Positive savings rate ({savings_rate:.1f}%), room to scale toward 20%.")
        else:
            patterns["concerns"].append("Negative savings rate: Outflows exceed total incoming revenue.")

        if net_flow > 0:
            patterns["strengths"].append(f"Healthy net monthly cash surplus: {format_currency(net_flow)}.")
        else:
            patterns["concerns"].append(f"Cash flow deficit: {format_currency(abs(net_flow))} monthly shortfall.")

        category_analysis = categorized_data.get("category_analysis", {})
        for cat, pct in category_analysis.items():
            if pct > 35.0:
                patterns["concerns"].append(f"High concentration in {cat} accounting for {pct:.1f}% of total spend.")

        return patterns

    def _calculate_financial_health_score(self, metrics: Dict[str, float]) -> int:
        score = 50
        savings_rate = metrics.get("savings_rate", 0.0)
        if savings_rate >= 20.0:
            score += 25
        elif savings_rate >= 10.0:
            score += 15
        elif savings_rate < 0.0:
            score -= 20

        fixed_ratio = metrics.get("fixed_expense_ratio", 0.0)
        if 0 < fixed_ratio <= 50.0:
            score += 15
        elif fixed_ratio > 60.0:
            score -= 15

        if metrics.get("net_cash_flow", 0.0) > 0:
            score += 10
        else:
            score -= 15

        return max(10, min(100, score))

    def _generate_comprehensive_insights(
        self,
        categorized: Dict[str, Any],
        metrics: Dict[str, float],
        patterns: Dict[str, Any],
    ) -> str:
        total_income = metrics.get("total_income", 0.0)
        total_expenses = metrics.get("total_expenses", 0.0)
        net_flow = metrics.get("net_cash_flow", 0.0)
        savings_rate = metrics.get("savings_rate", 0.0)

        top_cats = sorted(categorized.get("category_analysis", {}).items(), key=lambda x: x[1], reverse=True)[:4]
        cat_lines = [f"- **{cat}**: {pct:.1f}% of expenditure" for cat, pct in top_cats] or ["- Transaction data insufficient."]

        strengths = patterns.get("strengths", [])
        concerns = patterns.get("concerns", [])
        opportunities = patterns.get("opportunities", [])

        lines = [
            "### Cash Flow & Transaction Health Assessment",
            "",
            f"- **Analyzed Total Inflow:** {format_currency(total_income)}",
            f"- **Analyzed Total Outflow:** {format_currency(total_expenses)}",
            f"- **Net Cash Flow:** {format_currency(net_flow)}",
            f"- **Realized Savings Rate:** {savings_rate:.1f}%",
            "",
            "#### Spending Mix by Category",
            *cat_lines,
            "",
            "#### Key Findings",
            *[f"- **Strength:** {s}" for s in strengths],
            *[f"- **Concern:** {c}" for c in concerns],
            *[f"- **Optimization:** {o}" for o in opportunities],
        ]
        return "\n".join(lines)

    def _get_empty_analysis(self) -> Dict[str, Any]:
        return {
            "categorized_data": {"categorized_transactions": {}, "spending_trends": {}, "anomalies": []},
            "financial_metrics": {"total_income": 0.0, "total_expenses": 0.0, "net_cash_flow": 0.0, "savings_rate": 0.0},
            "patterns_detected": {"strengths": [], "concerns": ["No transactions logged."], "opportunities": []},
            "insights": "No transactions have been recorded yet. Add transactions to see breakdown.",
            "summary_metrics": {"net_cash_flow": 0.0, "savings_rate": 0.0, "total_income": 0.0, "total_expenses": 0.0},
            "health_score": 50,
        }
