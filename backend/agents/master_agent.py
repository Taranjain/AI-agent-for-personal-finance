import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings
from graph.state import AnalysisType
from tools.calculators import format_currency
from tools.plan_builder import PlanInputs, build_plan, render_plan_markdown

logger = logging.getLogger("finwise.agents.master_agent")


class MasterFinancialStrategistAgent:
    """Coordinates deterministic routing, specialist synthesis, and anti-hallucination guardrails."""

    def __init__(self):
        self._llm = None
        self._system_prompt = SystemMessage(
            content=(
                "You are the Master Financial Strategist. "
                "Synthesize specialist financial analyses into a coherent, highly actionable personal financial plan. "
                "Be encouraging, concise, practical, and clear. "
                "CRITICAL: Never hallucinate or alter any numeric figures, percentages, or currency values."
            )
        )

    def _get_llm(self, model_name: Optional[str] = None):
        """Lazy initialization of Gemini LLM with model fallback support."""
        name = model_name or settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=name,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=1024,
                    max_retries=2,
                    request_timeout=60.0,
                )
            except Exception as exc:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI with %s: %s", name, exc)
        return None

    def determine_analysis_type(
        self,
        user_input: str,
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_summary: Optional[str] = None,
    ) -> AnalysisType:
        """Deterministic keyword-based intent classification and routing (no LLM call required)."""
        text = (user_input or "").lower().strip()
        has_profile = bool(user_profile)

        context_parts: List[str] = []
        if session_summary:
            context_parts.append(str(session_summary))
        if conversation_history:
            for msg in reversed(conversation_history):
                if str(msg.get("role", "")).lower() == "user" and msg.get("content"):
                    context_parts.append(str(msg.get("content")))
                    break

        enriched_text = f"{text} {' '.join(context_parts)}".strip().lower() if context_parts else text

        # Check for educational intent
        education_patterns = [
            r"\bwhat is\b", r"\bwhat are\b", r"\bhow does\b", r"\bhow do\b",
            r"\bexplain\b", r"\bdefine\b", r"\bmeaning of\b", r"\bteach me\b",
        ]
        looks_educational = any(re.search(pat, enriched_text) for pat in education_patterns)

        # Personal action keywords
        personal_patterns = [
            r"\bmy\b", r"\bi\b", r"\bshould i\b", r"\bhelp me\b", r"\boptimi[sz]e\b",
            r"\bfor me\b", r"\bwhat should i\b", r"\bcan i\b", r"\bmy portfolio\b",
        ]
        personal_intent = any(re.search(pat, text) for pat in personal_patterns)

        domain_keywords = {
            AnalysisType.INCOME_EXPENSE: [
                "expense", "spend", "spending", "income", "cash flow", "cashflow", "transaction", "outflow",
            ],
            AnalysisType.BUDGET_PLANNING: [
                "budget", "save", "savings", "allocation", "monthly plan", "cut costs", "runway",
            ],
            AnalysisType.INVESTMENT_ADVICE: [
                "invest", "portfolio", "stock", "etf", "mutual fund", "sip", "returns", "asset allocation",
            ],
            AnalysisType.DEBT_OPTIMIZATION: [
                "debt", "loan", "credit card", "interest", "repay", "repayment", "emi", "avalanche", "snowball",
            ],
        }

        scores = {atype: 0 for atype in domain_keywords}
        for atype, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in enriched_text:
                    scores[atype] += 1

        non_zero_domains = [d for d, s in scores.items() if s > 0]
        comprehensive_keywords = [
            "full analysis", "comprehensive", "overall", "financial plan", "complete roadmap", "my finances",
        ]
        has_comprehensive_kw = any(ckw in text for ckw in comprehensive_keywords)

        if looks_educational and not personal_intent and len(non_zero_domains) == 0:
            return AnalysisType.FINANCIAL_EDUCATION

        if looks_educational and not has_profile:
            return AnalysisType.FINANCIAL_EDUCATION

        if has_comprehensive_kw or len(non_zero_domains) >= 2:
            return AnalysisType.COMPREHENSIVE

        if len(non_zero_domains) == 1:
            return non_zero_domains[0]

        if not has_profile:
            return AnalysisType.FINANCIAL_EDUCATION

        return AnalysisType.COMPREHENSIVE

    def synthesize_plan(
        self,
        user_profile: Optional[Dict[str, Any]],
        analyses: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesize specialist outputs into a master plan with LLM narrative and anti-hallucination guardrail."""
        logger.info("MasterAgent synthesizing plan across %d specialist analyses", len(analyses))

        valid_analyses = {k: v for k, v in analyses.items() if v and not v.get("error")}
        currency_code = str((user_profile or {}).get("currency") or "INR").upper()

        inputs = PlanInputs(
            user_profile=user_profile if user_profile else None,
            income_analysis=valid_analyses.get("income_analysis"),
            budget_plan=valid_analyses.get("budget_plan"),
            investment_advice=valid_analyses.get("investment_advice"),
            debt_optimization=valid_analyses.get("debt_optimization"),
        )
        structured_plan = build_plan(inputs)
        deterministic_markdown = render_plan_markdown(structured_plan, currency_code=currency_code)

        final_markdown = deterministic_markdown
        fallback_used = False

        # Attempt LLM polish if enabled
        narrative_enabled = True
        if context and isinstance(context, dict):
            options = context.get("options", {})
            if isinstance(options, dict) and options.get("narrative") is False:
                narrative_enabled = False

        final_markdown = deterministic_markdown
        fallback_used = True

        candidate_models = [settings.MODEL_NAME]

        if narrative_enabled and settings.GOOGLE_API_KEY:
            rewrite_prompt = f"""
You are the Master Financial Strategist. Rewrite the following financial plan to make it cohesive, engaging, and easy to understand for the user.

STRICT ACCURACY RULES (Zero Tolerance for Hallucinations):
- Do NOT introduce any new numbers, percentages, interest rates, or currency values.
- Keep EVERY existing numerical value, timeline, and metric exactly as shown.
- Maintain the section structure (Executive Summary, Key Metrics, Actions).
- Keep the rewritten synthesis concise and focused (under 400 words) while covering all sections.
- Tone: Empathetic, expert, clear, encouraging.

PLAN CONTENT TO REWRITE:
{deterministic_markdown}
"""
            for m_name in candidate_models:
                llm = self._get_llm(m_name)
                if not llm:
                    continue
                try:
                    response = llm.invoke([self._system_prompt, HumanMessage(content=rewrite_prompt)])
                    candidate = response.content.strip() if hasattr(response, "content") else str(response)

                    # Anti-hallucination guardrail check
                    if self._numbers_are_subset(candidate, deterministic_markdown):
                        final_markdown = candidate
                        fallback_used = False
                    else:
                        logger.warning("LLM output introduced new numbers; falling back to deterministic markdown.")
                        final_markdown = deterministic_markdown
                        fallback_used = True
                    break
                except Exception as exc:
                    logger.warning("Synthesis LLM error with model %s: %s", m_name, exc)
                    continue

        plan_dict = structured_plan.model_dump()
        return {
            "response": final_markdown,
            "agent": "master",
            "actionType": self._determine_action_type(valid_analyses),
            "priority": self._determine_priority(valid_analyses),
            "insights": self._extract_key_insights(valid_analyses, currency_code),
            "fallback_used": fallback_used,
            "plan": plan_dict,
            "tool_calls": self._build_tool_calls(plan_dict, user_profile),
        }

    def _numbers_are_subset(self, candidate: str, reference: str) -> bool:
        """Anti-hallucination guardrail: every number in candidate must exist in reference."""
        reference_nums = self._extract_numbers(reference)
        candidate_nums = self._extract_numbers(candidate)
        return candidate_nums.issubset(reference_nums)

    def _extract_numbers(self, text: str) -> set:
        tokens = re.findall(r"[₹$]?\d[\d,]*(?:\.\d+)?%?", text)
        normalized = set()
        for token in tokens:
            cleaned = token.replace("₹", "").replace("$", "").replace(",", "").strip()
            if cleaned:
                normalized.add(cleaned)
        return normalized

    def _determine_action_type(self, analyses: Dict[str, Any]) -> str:
        if "debt_optimization" in analyses:
            return "manage_debt"
        if "investment_advice" in analyses:
            return "invest"
        if "budget_plan" in analyses:
            return "review_budget"
        if "income_analysis" in analyses:
            return "optimize_spending"
        return "comprehensive_review"

    def _determine_priority(self, analyses: Dict[str, Any]) -> str:
        if "debt_optimization" in analyses:
            debt_ratio = analyses["debt_optimization"].get("current_debt_situation", {}).get("debt_to_income_ratio", 0)
            if debt_ratio > 30:
                return "high"

        if "income_analysis" in analyses:
            net_flow = analyses["income_analysis"].get("summary_metrics", {}).get("net_cash_flow", 0)
            if net_flow < 0:
                return "high"

        return "medium"

    def _extract_key_insights(self, analyses: Dict[str, Any], currency: str = "INR") -> List[Dict[str, Any]]:
        insights = []

        if "income_analysis" in analyses:
            summary = analyses["income_analysis"].get("summary_metrics", {})
            net_flow = summary.get("net_cash_flow", 0.0)
            insights.append({
                "agent": "income_analyzer",
                "title": "Monthly Cash Flow",
                "description": f"Net cash flow stands at {format_currency(net_flow, currency)}.",
                "actionType": "optimize_spending" if net_flow < 0 else "increase_savings",
            })

        if "budget_plan" in analyses:
            rate = analyses["budget_plan"].get("savings_rate", 0.0)
            insights.append({
                "agent": "budget_planner",
                "title": "Savings Velocity",
                "description": f"Targeting a savings rate of {rate:.1f}% under recommended allocation.",
                "actionType": "review_budget",
            })

        if "debt_optimizer" in analyses:
            strat = analyses["debt_optimizer"].get("recommended_strategy", {})
            method = strat.get("recommended_method", "avalanche").capitalize()
            savings = strat.get("interest_savings", 0.0)
            insights.append({
                "agent": "debt_optimizer",
                "title": "Debt Acceleration",
                "description": f"Recommended {method} method with projected interest savings of {format_currency(savings, currency)}.",
                "actionType": "manage_debt",
            })

        if "investment_advice" in analyses:
            risk = str(analyses["investment_advice"].get("risk_profile", "moderate")).upper()
            insights.append({
                "agent": "investment_advisor",
                "title": "Portfolio Strategy",
                "description": f"Aligned with {risk} risk profile for inflation-beating compounding.",
                "actionType": "invest",
            })

        return insights

    def _build_tool_calls(self, plan: Dict[str, Any], user_profile: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Construct deterministic action steps and automation suggestions."""
        tools = []
        if not user_profile:
            return tools

        km = plan.get("key_metrics", {})
        net_flow = km.get("monthly_net_cash_flow")
        fund_months = km.get("emergency_fund_months")
        total_debt = km.get("total_debt")

        # 1. Weekly review cadence
        tools.append({
            "id": self._hash_id("weekly-checkin"),
            "title": "Schedule Weekly Expense Check-in",
            "description": "Establishes a weekly calendar checkpoint to review transactions and adjust category budgets.",
            "category": "habit",
        })

        # 2. Emergency fund top-up if runway low
        if fund_months is not None and fund_months < 6:
            tools.append({
                "id": self._hash_id("emergency-fund-automation"),
                "title": "Set Up Auto-SIP for Emergency Fund",
                "description": "Automate recurring transfers into a liquid fund until 6 months of buffer is reached.",
                "category": "savings",
            })

        # 3. Debt prepayment if debt exists
        if total_debt is not None and total_debt > 0:
            tools.append({
                "id": self._hash_id("debt-payoff-standing-instruction"),
                "title": "Enable Accelerated Debt Prepayment",
                "description": "Set a standing instruction for extra monthly debt principal reduction.",
                "category": "debt",
            })

        return tools

    def _hash_id(self, seed: str) -> str:
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
