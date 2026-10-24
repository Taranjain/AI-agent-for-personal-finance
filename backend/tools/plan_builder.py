from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from tools.calculators import format_currency


class KeyMetrics(BaseModel):
    monthly_net_cash_flow: Optional[float] = None
    savings_rate: Optional[float] = None
    debt_to_income: Optional[float] = None
    emergency_fund_months: Optional[float] = None
    total_debt: Optional[float] = None


class ActionItem(BaseModel):
    title: str
    why: str
    steps: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"] = "medium"
    expected_impact: str
    kind: Literal["cashflow", "budget", "debt", "invest", "goal", "education", "generic"] = "generic"
    due_days: Optional[int] = None
    id: Optional[str] = None


class ActionBuckets(BaseModel):
    next_7_days: List[ActionItem] = Field(default_factory=list)
    next_30_days: List[ActionItem] = Field(default_factory=list)
    next_12_months: List[ActionItem] = Field(default_factory=list)


class Plan(BaseModel):
    executive_summary: str
    key_metrics: KeyMetrics = Field(default_factory=KeyMetrics)
    actions: ActionBuckets = Field(default_factory=ActionBuckets)
    assumptions: List[str] = Field(default_factory=list)
    data_warnings: List[str] = Field(default_factory=list)


@dataclass(frozen=True)
class PlanInputs:
    user_profile: Optional[Dict[str, Any]]
    income_analysis: Optional[Dict[str, Any]] = None
    budget_plan: Optional[Dict[str, Any]] = None
    investment_advice: Optional[Dict[str, Any]] = None
    debt_optimization: Optional[Dict[str, Any]] = None
    financial_education: Optional[Dict[str, Any]] = None


def _safe_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _round_or_none(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (ValueError, TypeError):
        return None


def _normalize_percent(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if 0 < value <= 1.0:
        return value * 100.0
    return value


def build_plan(inputs: PlanInputs) -> Plan:
    """Build a comprehensive, deterministic structured financial plan from specialist agent outputs."""
    warnings: List[str] = []
    assumptions: List[str] = [
        "Emergency fund target uses 6 months of expenses baseline unless configured otherwise.",
        "Debt-to-income uses minimum required monthly payments relative to gross monthly income.",
    ]

    user_profile = inputs.user_profile or {}
    has_profile = bool(inputs.user_profile)
    currency_code = str(user_profile.get("currency") or "INR").upper()

    annual_income = _safe_float(user_profile.get("annual_income"))
    monthly_income = annual_income / 12.0 if annual_income is not None else None
    monthly_expenses = _safe_float(user_profile.get("monthly_expenses"))
    savings = _safe_float(user_profile.get("savings"))

    key_metrics = KeyMetrics()

    # Cash flow and savings rate from income analysis if available
    income_summary = None
    if inputs.income_analysis and not inputs.income_analysis.get("error"):
        income_summary = inputs.income_analysis.get("summary_metrics") or inputs.income_analysis.get("financial_metrics")

    if isinstance(income_summary, dict):
        key_metrics.monthly_net_cash_flow = _round_or_none(_safe_float(income_summary.get("net_cash_flow")))
        key_metrics.savings_rate = _round_or_none(_normalize_percent(_safe_float(income_summary.get("savings_rate"))))

    # Fallback to profile values if not present
    if key_metrics.monthly_net_cash_flow is None and monthly_income is not None and monthly_expenses is not None:
        key_metrics.monthly_net_cash_flow = _round_or_none(monthly_income - monthly_expenses)

    if key_metrics.savings_rate is None and monthly_income is not None and monthly_income > 0 and key_metrics.monthly_net_cash_flow is not None:
        key_metrics.savings_rate = _round_or_none((key_metrics.monthly_net_cash_flow / monthly_income) * 100.0)

    # Debts
    if inputs.debt_optimization and not inputs.debt_optimization.get("error"):
        debt_sit = inputs.debt_optimization.get("current_debt_situation", {})
        if isinstance(debt_sit, dict):
            key_metrics.total_debt = _round_or_none(_safe_float(debt_sit.get("total_debt")))
            key_metrics.debt_to_income = _round_or_none(_normalize_percent(_safe_float(debt_sit.get("debt_to_income_ratio"))))
    else:
        debts = user_profile.get("debts") if isinstance(user_profile.get("debts"), list) else []
        total_debt = sum(_safe_float(d.get("balance")) or 0.0 for d in debts)
        key_metrics.total_debt = _round_or_none(total_debt)
        if monthly_income and monthly_income > 0:
            total_min_pay = sum(_safe_float(d.get("minimum_payment")) or 0.0 for d in debts)
            key_metrics.debt_to_income = _round_or_none((total_min_pay / monthly_income) * 100.0)

    # Emergency fund runway
    if savings is not None and monthly_expenses is not None and monthly_expenses > 0:
        key_metrics.emergency_fund_months = _round_or_none(savings / monthly_expenses, 1)

    # Executive Summary Construction
    if inputs.financial_education and isinstance(inputs.financial_education, dict):
        concept = str(inputs.financial_education.get("concept_explained") or "financial planning")
        executive_summary = f"Financial education guide on: {concept}."
    elif not has_profile:
        executive_summary = "Set up your income, expenses, debts, and goals to generate a personalized action plan."
        warnings.append("No active financial profile found; generated recommendations are generalized.")
    else:
        parts: List[str] = []
        net_flow = key_metrics.monthly_net_cash_flow
        fund_months = key_metrics.emergency_fund_months
        total_debt = key_metrics.total_debt

        if net_flow is not None:
            if net_flow < 0:
                parts.append("Cash flow is negative; spending stabilization is the immediate priority.")
            elif net_flow == 0:
                parts.append("Cash flow is break-even; optimizing discretionary spend will unlock investment capital.")
            else:
                parts.append(f"Cash flow is positive with monthly surplus of {format_currency(net_flow, currency_code)}.")

        if fund_months is not None:
            if fund_months < 3:
                parts.append(f"Emergency runway is at {fund_months} months (target 6 months); strengthening liquid reserves is crucial.")
            else:
                parts.append(f"Emergency buffer is healthy at {fund_months} months of expenses.")

        if total_debt is not None and total_debt > 0:
            parts.append(f"Outstanding debt total is {format_currency(total_debt, currency_code)}; an accelerated payoff strategy is recommended.")

        executive_summary = " ".join(parts) if parts else "Financial plan synthesized based on your current financial profile."

    actions = _build_actions(
        key_metrics=key_metrics,
        user_profile=user_profile,
        budget_plan=inputs.budget_plan,
        debt_optimization=inputs.debt_optimization,
        currency_code=currency_code,
        warnings=warnings,
    )

    return Plan(
        executive_summary=executive_summary,
        key_metrics=key_metrics,
        actions=actions,
        assumptions=assumptions,
        data_warnings=warnings,
    )


def _build_actions(
    key_metrics: KeyMetrics,
    user_profile: Dict[str, Any],
    budget_plan: Optional[Dict[str, Any]],
    debt_optimization: Optional[Dict[str, Any]],
    currency_code: str,
    warnings: List[str],
) -> ActionBuckets:
    buckets = ActionBuckets()

    def add(bucket: List[ActionItem], item: ActionItem, bucket_days: int) -> None:
        if item.due_days is None:
            item.due_days = bucket_days
        if not item.id:
            digest = hashlib.sha256(f"{bucket_days}|{item.title}".encode("utf-8")).hexdigest()
            item.id = digest[:12]
        bucket.append(item)

    if not user_profile:
        add(
            buckets.next_7_days,
            ActionItem(
                title="Complete your financial profile",
                why="Actionable advice requires knowing income, expenses, debts, and timeline goals.",
                steps=[
                    "Enter monthly income and living expenses",
                    "List all existing debt balances and interest rates",
                    "Add 1 to 3 personal financial goals",
                ],
                priority="high",
                expected_impact="Unlocks precision analysis and tailored recommendations.",
                kind="generic",
            ),
            bucket_days=7,
        )
        return buckets

    net_flow = key_metrics.monthly_net_cash_flow
    fund_months = key_metrics.emergency_fund_months
    total_debt = key_metrics.total_debt

    # Cash flow correction
    if net_flow is not None and net_flow < 0:
        add(
            buckets.next_7_days,
            ActionItem(
                title="Control monthly cash outflow",
                why="Negative cash flow accumulates debt and depletes savings reserves.",
                steps=[
                    "Audit top 3 discretionary spending categories",
                    "Establish weekly spending caps on dining, leisure, and shopping",
                    "Cancel unused recurring subscriptions and memberships",
                ],
                priority="high",
                expected_impact="Restores cash flow to positive territory within 30 days.",
                kind="cashflow",
            ),
            bucket_days=7,
        )

    # Emergency fund action
    if fund_months is not None and fund_months < 6:
        add(
            buckets.next_30_days,
            ActionItem(
                title="Build emergency liquidity buffer",
                why="An emergency cushion protects against unexpected healthcare or career disruptions.",
                steps=[
                    "Open a high-yield liquid savings account or sweep-in deposit",
                    "Automate a fixed transfer right on salary credit day",
                    "Preserve emergency funds strictly for unforeseen essentials",
                ],
                priority="high",
                expected_impact="Builds safety runway toward the recommended 6-month target.",
                kind="cashflow",
            ),
            bucket_days=30,
        )

    # Debt payoff action
    if total_debt is not None and total_debt > 0:
        method = "Avalanche"
        if debt_optimization and isinstance(debt_optimization, dict):
            recommended = debt_optimization.get("recommended_strategy", {})
            if isinstance(recommended, dict) and recommended.get("recommended_method"):
                method = str(recommended.get("recommended_method")).capitalize()

        add(
            buckets.next_30_days,
            ActionItem(
                title=f"Execute {method} debt repayment strategy",
                why="Targeting high-cost debt provides guaranteed risk-free financial return.",
                steps=[
                    "Ensure minimum payments on all loans are scheduled automatically",
                    f"Direct extra monthly surplus toward the priority debt via {method} method",
                    "Refinance or consolidate high-rate credit balances if interest exceeds 15%",
                ],
                priority="high",
                expected_impact="Shortens repayment timeline and saves significant interest.",
                kind="debt",
            ),
            bucket_days=30,
        )

    # Goal savings action
    if budget_plan and isinstance(budget_plan, dict) and not budget_plan.get("error"):
        savings_plan = budget_plan.get("savings_plan", {})
        monthly_goal_savings = _safe_float(savings_plan.get("total_monthly_savings") if isinstance(savings_plan, dict) else None)
        if monthly_goal_savings and monthly_goal_savings > 0:
            add(
                buckets.next_7_days,
                ActionItem(
                    title="Automate goal-oriented monthly savings",
                    why="Systematic transfers ensure goals are funded before lifestyle creep occurs.",
                    steps=[
                        f"Set up standing instructions for {format_currency(monthly_goal_savings, currency_code)} per month",
                        "Align each bucket to specific target dates",
                    ],
                    priority="medium",
                    expected_impact="Guarantees disciplined progress toward life goals.",
                    kind="goal",
                ),
                bucket_days=7,
            )

    # Investment action
    if net_flow is None or net_flow >= 0:
        add(
            buckets.next_12_months,
            ActionItem(
                title="Systematic long-term portfolio compounding",
                why="Disciplined regular investing hedges against inflation and compounds wealth.",
                steps=[
                    "Establish a recurring monthly SIP in broad-market index and mutual funds",
                    "Maintain risk-appropriate asset allocation between equity and fixed income",
                    "Conduct semi-annual rebalancing to re-align portfolio weights",
                ],
                priority="medium",
                expected_impact="Capitalizes on compounding to achieve long-term financial independence.",
                kind="invest",
            ),
            bucket_days=365,
        )

    return buckets


def render_plan_markdown(plan: Plan, currency_code: str = "INR") -> str:
    """Format structured Plan object into a clean Markdown report."""
    km = plan.key_metrics
    lines: List[str] = [
        "# Financial Strategy & Action Plan",
        "---",
        "",
        "## 1. Executive Summary",
        plan.executive_summary.strip(),
        "",
        "## 2. Key Metrics Snapshot",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Monthly Net Cash Flow | {format_currency(km.monthly_net_cash_flow, currency_code)} |",
        f"| Savings Rate | {f'{km.savings_rate:.1f}%' if km.savings_rate is not None else '-'} |",
        f"| Debt-to-Income (Min Payments) | {f'{km.debt_to_income:.1f}%' if km.debt_to_income is not None else '-'} |",
        f"| Emergency Fund Runway | {f'{km.emergency_fund_months:.1f} months' if km.emergency_fund_months is not None else '-'} |",
        f"| Total Debt Balance | {format_currency(km.total_debt, currency_code)} |",
        "",
        "## 3. Prioritized Action Plan",
        "",
    ]

    lines.extend(_render_action_bucket("Immediate Focus (Next 7 Days)", plan.actions.next_7_days))
    lines.extend(_render_action_bucket("Short-Term Focus (Next 30 Days)", plan.actions.next_30_days))
    lines.extend(_render_action_bucket("Long-Term Strategy (Next 12 Months)", plan.actions.next_12_months))

    if plan.data_warnings:
        lines.append("## 4. Observations & Data Warnings")
        for w in plan.data_warnings:
            lines.append(f"- {w}")
        lines.append("")

    if plan.assumptions:
        lines.append("## 5. Underlying Assumptions")
        for a in plan.assumptions:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _render_action_bucket(title: str, items: List[ActionItem]) -> List[str]:
    if not items:
        return [f"### {title}", "- *No immediate actions required in this timeframe.*", ""]

    lines = [f"### {title}"]
    for item in items:
        lines.append(f"- **{item.title}** [`{item.priority.upper()}` priority] — {item.why}")
        for step in item.steps:
            lines.append(f"  - {step}")
        lines.append(f"  - **Impact:** {item.expected_impact}")
    lines.append("")
    return lines
