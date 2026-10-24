import logging
from collections import OrderedDict
from time import time
from typing import Any, Dict, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings

logger = logging.getLogger("finwise.agents.financial_educator")


FALLBACK_EDUCATION_EXPLANATION = """
### Financial Literacy Concept Overview

1. **Definition**: Financial literacy is the ability to understand and effectively apply various financial skills, including personal financial management, budgeting, investing, and debt management.
2. **Why it matters**: Strong financial fundamentals ensure that you preserve purchasing power against inflation, build emergency safety nets, and systematically achieve long-term financial independence.
3. **Simple Example**: By investing ₹5,000 monthly in a diversified fund compounding at 12% annual return, you accumulate over ₹11.6 Lakhs in 10 years, where more than ₹5.6 Lakhs is pure compounded growth!
"""


class FinancialEducatorAgent:
    """Specialist agent providing clear educational guidance on financial topics and instruments."""

    _CACHE_MAX_SIZE = 128
    _CACHE_TTL_SECONDS = 3600  # 1 hour

    def __init__(self):
        self._concept_cache: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()
        self._llm = None
        self._system_prompt = SystemMessage(
            content=(
                "You are an encouraging, expert Financial Educator. "
                "Explain financial concepts clearly, concisely, and practically. "
                "Always format your response with: "
                "1) Clear Definition, 2) Why It Matters, 3) Real-world Example (using INR ₹ where applicable). "
                "Keep your explanation concise (under 250 words) and beginner-friendly."
            )
        )

    def _get_llm(self, model_name: Optional[str] = None):
        """Lazy initialization of Gemini LLM with candidate model support."""
        name = model_name or settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=name,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.3,
                    max_output_tokens=1024,
                    max_retries=2,
                    request_timeout=45.0,
                )
            except Exception as exc:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI (%s): %s", name, exc)
        return None

    def explain_concept(self, user_input: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Explain a financial concept with optional user profile relevance."""
        logger.info("FinancialEducatorAgent explaining concept for query: %s", (user_input or "")[:50])

        clean_text = (user_input or "").lower().strip()
        if clean_text in ["hi", "hello", "hey", "help", "start", "greetings"]:
            return {
                "concept_explained": "Introduction",
                "explanation": (
                    "Hello! 👋 I am your FinWise Financial Education Assistant.\n\n"
                    "Ask me about any financial concept, metric, or strategy. For example:\n"
                    "- *'What is compound interest?'*\n"
                    "- *'Explain SIP vs Lump Sum investing'*\n"
                    "- *'How does the Debt Avalanche method work?'*\n"
                    "- *'What is the 50/30/20 rule?'*\n\n"
                    "What would you like to explore today?"
                ),
                "fallback_used": False,
            }

        concept = self._extract_concept(user_input)
        cached = self._cache_get(concept)
        if cached is not None:
            return cached

        profile_context = self._format_profile_context(user_profile)
        prompt_text = f"""
Explain the concept: "{concept}"

User Context (for practical relevance only):
{profile_context}

User Question:
"{user_input}"

Format requirements:
1) Definition
2) Why It Matters
3) Practical Example (use INR values where appropriate)
"""
        explanation = None
        fallback_used = False

        candidate_models = [settings.MODEL_NAME]

        if settings.GOOGLE_API_KEY:
            for m_name in candidate_models:
                llm = self._get_llm(m_name)
                if not llm:
                    continue
                try:
                    response = llm.invoke([self._system_prompt, HumanMessage(content=prompt_text)])
                    explanation = response.content.strip() if hasattr(response, "content") else str(response)
                    fallback_used = False
                    break
                except Exception as exc:
                    logger.warning("FinancialEducatorAgent LLM invocation failed with %s: %s", m_name, exc)
                    fallback_used = True

        if not explanation:
            explanation = self._build_deterministic_explanation(concept)
            fallback_used = True

        result = {
            "concept_explained": concept,
            "explanation": explanation,
            "fallback_used": fallback_used,
        }

        self._cache_set(concept, result)
        return result

    def _extract_concept(self, user_input: str) -> str:
        text = (user_input or "").lower().strip()
        common_terms = [
            "compound interest", "emergency fund", "mutual fund", "sip", "systematic investment plan",
            "stock", "equity", "debt", "bond", "inflation", "index fund", "snowball", "avalanche",
            "credit score", "cibil", "fixed deposit", "liquid fund", "ppf", "nps", "rebalancing",
            "tax saving", "budget", "net worth", "diversification", "asset allocation", "emi",
        ]
        for term in common_terms:
            if term in text:
                return term

        for prefix in ["what is ", "what are ", "how does ", "how do ", "explain ", "tell me about ", "what's "]:
            if text.startswith(prefix):
                return user_input[len(prefix):].strip("? .")

        return user_input[:50] if user_input else "Personal Finance Fundamentals"

    def _format_profile_context(self, user_profile: Optional[Dict[str, Any]]) -> str:
        if not user_profile:
            return "No profile context available."
        parts = []
        if user_profile.get("age"):
            parts.append(f"Age: {user_profile['age']}")
        if user_profile.get("risk_tolerance"):
            parts.append(f"Risk Profile: {user_profile['risk_tolerance']}")
        if user_profile.get("investment_experience"):
            parts.append(f"Experience: {user_profile['investment_experience']}")
        return ", ".join(parts) if parts else "General profile."

    def _build_deterministic_explanation(self, concept: str) -> str:
        concept_title = concept.title()
        return f"""
### {concept_title} — Educational Summary

1. **Definition**: **{concept_title}** is a core personal finance instrument/strategy designed to optimize how your money is protected, managed, or grown over time.
2. **Why It Matters**: Understanding {concept_title} allows you to make informed decisions, minimize avoidable financing costs, and build sustainable financial resilience.
3. **Practical Example**: For example, integrating {concept_title} into your monthly routine helps allocate cash surplus systematically rather than leaving money idle or overspending on discretionary purchases.
"""

    def _cache_get(self, concept: str) -> Optional[Dict[str, Any]]:
        entry = self._concept_cache.get(concept)
        if not entry:
            return None
        timestamp, payload = entry
        if time() - timestamp > self._CACHE_TTL_SECONDS:
            del self._concept_cache[concept]
            return None
        self._concept_cache.move_to_end(concept)
        return dict(payload)

    def _cache_set(self, concept: str, payload: Dict[str, Any]) -> None:
        self._concept_cache[concept] = (time(), dict(payload))
        self._concept_cache.move_to_end(concept)
        while len(self._concept_cache) > self._CACHE_MAX_SIZE:
            self._concept_cache.popitem(last=False)
