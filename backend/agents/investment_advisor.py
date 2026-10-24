import logging
from typing import Any, Dict
from tools.calculators import FinancialCalculators, RiskProfile, format_currency

logger = logging.getLogger("finwise.agents.investment_advisor")


class InvestmentAdvisorAgent:
    """Specialist agent providing goal-based portfolio asset allocation and return projections."""

    def __init__(self):
        self.calculators = FinancialCalculators()

    def provide_advice(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive asset allocation model and compounded projection."""
        logger.info("InvestmentAdvisorAgent generating strategy for profile")

        try:
            risk_profile = self._assess_risk_profile(user_profile)
            strategy = self._create_investment_strategy(user_profile, risk_profile)
            portfolio = self._create_portfolio_allocation(risk_profile, user_profile)
            expected_returns = self._calculate_expected_returns(portfolio, risk_profile)
            recommendations = self._generate_recommendations(user_profile, risk_profile, strategy, portfolio)

            return {
                "risk_profile": risk_profile.value,
                "investment_strategy": strategy,
                "portfolio_allocation": portfolio,
                "expected_returns": expected_returns,
                "recommendations": recommendations,
                "time_horizon": int(user_profile.get("time_horizon", 10)),
            }
        except Exception as exc:
            logger.error("Error generating investment advice: %s", exc)
            return {
                "error": str(exc),
                "recommendations": "Unable to compute investment strategy due to invalid profile data.",
            }

    def _assess_risk_profile(self, user_profile: Dict[str, Any]) -> RiskProfile:
        age = int(user_profile.get("age", 28))
        risk_tolerance = str(user_profile.get("risk_tolerance", "moderate"))
        experience = str(user_profile.get("investment_experience", "beginner"))
        time_horizon = int(user_profile.get("time_horizon", 5))

        return self.calculators.assess_risk_profile(
            age=age,
            investment_experience=experience,
            time_horizon=time_horizon,
            risk_tolerance=risk_tolerance,
        )

    def _create_investment_strategy(self, user_profile: Dict[str, Any], risk_profile: RiskProfile) -> Dict[str, Any]:
        age = int(user_profile.get("age", 28))
        time_horizon = int(user_profile.get("time_horizon", 5))

        strategies = {
            RiskProfile.CONSERVATIVE: {
                "name": "Capital Preservation & Income",
                "focus": "Low-volatility principal protection with fixed income yields",
                "approach": "Heavy allocation to sovereign debt, fixed deposits, and short-term debt funds",
                "rebalancing": "Annual review with threshold rebalancing at 5% drift",
            },
            RiskProfile.MODERATE: {
                "name": "Balanced Wealth Accumulation",
                "focus": "Healthy capital appreciation while tempering market downturns",
                "approach": "65% equities (Large & Mid-cap index funds) + 35% fixed income & gold",
                "rebalancing": "Semi-annual review with tactical SIP re-allocations",
            },
            RiskProfile.AGGRESSIVE: {
                "name": "Long-Term Growth Maximization",
                "focus": "Aggressive capital compounding over multi-year horizons",
                "approach": "85% equities (Broad market, Flexi-cap, International ETFs) + 15% debt buffer",
                "rebalancing": "Quarterly portfolio drift check",
            },
        }

        strat = dict(strategies.get(risk_profile, strategies[RiskProfile.MODERATE]))
        if age < 35 and time_horizon >= 10:
            strat["tilt"] = "Long horizon allows sustained equity compounding through full market cycles."
        elif age > 50:
            strat["tilt"] = "Gradually transition maturing equity gains into safe liquid fixed instruments."

        return strat

    def _create_portfolio_allocation(self, risk_profile: RiskProfile, user_profile: Dict[str, Any]) -> Dict[str, float]:
        base_allocations = {
            RiskProfile.CONSERVATIVE: {
                "Domestic Large-Cap Equity": 25.0,
                "International Equity": 10.0,
                "Government & Corporate Bonds": 45.0,
                "Gold / Sovereign Gold Bonds": 10.0,
                "Liquid Cash / Sweep-in": 10.0,
            },
            RiskProfile.MODERATE: {
                "Domestic Large-Cap Equity": 40.0,
                "Mid & Small-Cap Equity": 15.0,
                "International Equity": 10.0,
                "Bonds & Debt Funds": 25.0,
                "Gold / Sovereign Gold Bonds": 7.0,
                "Liquid Cash": 3.0,
            },
            RiskProfile.AGGRESSIVE: {
                "Domestic Large-Cap Equity": 45.0,
                "Mid & Small-Cap Equity": 25.0,
                "International / Tech Equity": 15.0,
                "Bonds & Debt Funds": 10.0,
                "Gold": 5.0,
            },
        }

        allocation = dict(base_allocations.get(risk_profile, base_allocations[RiskProfile.MODERATE]))
        if user_profile.get("investment_experience") == "advanced":
            allocation["Alternative Investments"] = 5.0
            if "Domestic Large-Cap Equity" in allocation:
                allocation["Domestic Large-Cap Equity"] -= 5.0

        return allocation

    def _calculate_expected_returns(self, portfolio: Dict[str, float], risk_profile: RiskProfile) -> Dict[str, float]:
        asset_expected_returns = {
            "Domestic Large-Cap Equity": 12.0,
            "Mid & Small-Cap Equity": 14.0,
            "International Equity": 11.0,
            "International / Tech Equity": 12.5,
            "Government & Corporate Bonds": 7.0,
            "Bonds & Debt Funds": 7.2,
            "Gold / Sovereign Gold Bonds": 8.0,
            "Gold": 8.0,
            "Liquid Cash / Sweep-in": 5.5,
            "Liquid Cash": 5.5,
            "Alternative Investments": 13.0,
        }

        weighted_annual = 0.0
        for asset, weight in portfolio.items():
            rate = asset_expected_returns.get(asset, 8.0)
            weighted_annual += (weight / 100.0) * rate

        # Expected inflation benchmark in India ~ 5.5%
        inflation_rate = 5.5
        real_return = weighted_annual - inflation_rate

        compounded_5yr = round(((1.0 + weighted_annual / 100.0) ** 5 - 1.0) * 100.0, 1)
        compounded_10yr = round(((1.0 + weighted_annual / 100.0) ** 10 - 1.0) * 100.0, 1)

        return {
            "expected_annual_return": round(weighted_annual, 2),
            "inflation_adjusted_return": round(real_return, 2),
            "compounded_5yr_growth_pct": compounded_5yr,
            "compounded_10yr_growth_pct": compounded_10yr,
        }

    def _generate_recommendations(
        self,
        user_profile: Dict[str, Any],
        risk_profile: RiskProfile,
        strategy: Dict[str, Any],
        portfolio: Dict[str, float],
    ) -> str:
        currency = str(user_profile.get("currency") or "INR")
        portfolio_lines = [f"- **{asset}**: {pct:.1f}%" for asset, pct in portfolio.items()]

        goals = user_profile.get("financial_goals", []) or []
        goal_lines = [
            f"- {g.get('name')}: Target {format_currency(float(g.get('target_amount') or g.get('target') or 0.0), currency)} (Horizon: {g.get('timeline_months', 12)} months)"
            for g in goals[:3]
        ] or ["- Formulate specific long-term milestone goals to tailor SIP horizons."]

        return "\n".join([
            "### Investment Asset Allocation Architecture",
            "",
            f"- **Assessed Risk Profile:** {risk_profile.value.upper()}",
            f"- **Investment Strategy:** {strategy.get('name')}",
            f"- **Core Focus:** {strategy.get('focus')}",
            "",
            "#### Target Asset Allocation Mix",
            *portfolio_lines,
            "",
            "#### Execution Guidelines",
            "1. Initiate disciplined monthly SIPs in low-cost index funds tracking benchmark indices (Nifty 50, Nifty Next 50).",
            "2. Utilize Sovereign Gold Bonds (SGBs) or Gold ETFs for the defensive commodity sleeve.",
            "3. Maintain short-term goal capital in high-grade liquid mutual funds rather than volatile equity.",
            "4. Review and rebalance portfolio allocations semi-annually if any asset class deviates by over 5%.",
            "",
            "#### Aligned Life Goals",
            *goal_lines,
        ])
