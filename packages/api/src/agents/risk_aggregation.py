"""
Risk Aggregation Agent — combines dimension scores into final assessment.

Uses LLM to synthesize individual agent results into a cohesive
risk summary with overall recommendation. Includes intelligent
lending strategies to reduce false denials and false approvals.
"""

import logging
from typing import Any

from .base import AgentResult, ApplicationData, BaseAgent

logger = logging.getLogger(__name__)


class RiskAggregationAgent(BaseAgent):
    """Aggregates all dimension scores and produces final risk summary."""

    dimension_name = "risk_aggregation"
    agent_name = "risk_aggregator"
    weight = 1.0  # Not used in weighted average — this is the final aggregator
    max_tokens = 2048

    def build_aggregation_prompt(
        self,
        data: ApplicationData,
        dimension_results: list[AgentResult],
    ) -> list[dict[str, str]]:
        """Build prompt that synthesizes all dimension results."""

        # Build dimension summary
        dim_summaries = []
        for r in dimension_results:
            status = "completed" if r.succeeded else f"error: {r.error}"
            dim_summaries.append(f"""
### {r.dimension_name.replace("_", " ").title()} (Weight: {r.weight:.0%})
- **Score:** {r.score:.1f}/100 ({status})
- **Positive Factors:** {"; ".join(r.positive_factors) if r.positive_factors else "None"}
- **Risk Factors:** {"; ".join(r.risk_factors) if r.risk_factors else "None"}
- **Mitigating Factors:** {"; ".join(r.mitigating_factors) if r.mitigating_factors else "None"}
""")

        # Calculate weighted average
        total_weighted = sum(r.weighted_score for r in dimension_results if r.succeeded)
        total_weight = sum(r.weight for r in dimension_results if r.succeeded)
        weighted_avg = total_weighted / total_weight if total_weight > 0 else 50

        system_msg = f"""You are a senior mortgage risk assessment AI. Your role is to synthesize
individual risk dimension analyses into a final comprehensive risk assessment.

You must respond with valid JSON matching this schema:
{{
  "overall_score": <number 0-100>,
  "risk_band": "<low|medium|high|critical>",
  "recommendation": "<approve|conditional_approve|review|deny>",
  "summary": "<2-3 sentence summary of the overall risk profile>",
  "key_strengths": [<top 3-5 most important positive factors>],
  "key_concerns": [<top 3-5 most important risk factors>],
  "conditions": [<list of conditions for conditional approval, if applicable>],
  "confidence": <number 0.0-1.0 indicating confidence in assessment>
}}

Risk band thresholds:
- 80+: low risk
- 60-79: medium risk
- 40-59: high risk
- below 40: critical risk

Recommendation guidelines:
- low risk (80+): "approve" (or "conditional_approve" if stress test concerns exist)
- medium risk (60-79): "review" or "conditional_approve" depending on compensating factors
- high risk (40-59): "review" (significant concerns need human judgment)
- critical risk (below 40): "deny"

IMPORTANT - False denial prevention:
- A borrower with past bankruptcy/foreclosure but 24+ months of clean payment history
  and strong income should NOT be automatically denied. Look for recovery trajectory.
- Strong compensating factors (high down payment, large reserves, low DTI) can offset
  poor credit history.

IMPORTANT - False approval prevention:
- A borrower with good credit but thin reserves, high DTI, or short employment
  history may be riskier than their score suggests.
- If fraud risk dimension scores above 60, escalate to "deny" regardless of other factors.
- Consider whether the borrower can sustain payments under stress (income drop, rate increase).

The weighted average of dimension scores is {weighted_avg:.1f}. You may adjust
the final score based on your holistic analysis, but explain significant deviations."""

        user_msg = f"""Synthesize the following risk dimension analyses into a final assessment:

## Application: {data.application_number}
- **Loan Product:** {data.loan_product_name} ({data.loan_product_type})
- **Loan Amount:** {self._format_currency(data.loan_amount)}
- **Down Payment:** {self._format_currency(data.down_payment)}
- **DTI Ratio:** {self._format_pct(data.dti_ratio)}

## Dimension Scores (Weighted Average: {weighted_avg:.1f})
{"".join(dim_summaries)}

## Analysis Request
Provide your final comprehensive risk assessment as JSON. Consider how the
different dimensions interact — for example, a low credit score combined with
high DTI is worse than either alone. Also consider any compensating factors
and recovery trajectories for borrowers with past credit events."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    def aggregate(
        self,
        data: ApplicationData,
        dimension_results: list[AgentResult],
    ) -> dict[str, Any]:
        """Run aggregation analysis using LLM with intelligent recommendation logic.

        Args:
            data: Application data.
            dimension_results: Results from all dimension agents.

        Returns:
            Dict with overall_score, risk_band, recommendation, summary, etc.
        """
        from ..services.llm_gateway import call_llm_json

        messages = self.build_aggregation_prompt(data, dimension_results)

        try:
            parsed, llm_response = call_llm_json(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Validate and clamp score
            parsed["overall_score"] = max(0, min(100, float(parsed.get("overall_score", 50))))

            # Validate risk band
            valid_bands = {"low", "medium", "high", "critical"}
            if parsed.get("risk_band") not in valid_bands:
                score = parsed["overall_score"]
                if score >= 80:
                    parsed["risk_band"] = "low"
                elif score >= 60:
                    parsed["risk_band"] = "medium"
                elif score >= 40:
                    parsed["risk_band"] = "high"
                else:
                    parsed["risk_band"] = "critical"

            # Validate recommendation (expanded set)
            valid_recs = {"approve", "conditional_approve", "review", "deny"}
            if parsed.get("recommendation") not in valid_recs:
                parsed["recommendation"] = "review"

            # Apply intelligent override logic
            parsed = self._apply_intelligent_overrides(parsed, dimension_results, data)

            parsed["tokens_used"] = llm_response.total_tokens
            parsed["latency_ms"] = llm_response.latency_ms

            return parsed

        except Exception as e:
            # Fallback to rule-based aggregation with intelligent logic
            return self._rule_based_aggregation(dimension_results, data, error=e)

    def _apply_intelligent_overrides(
        self,
        parsed: dict[str, Any],
        dimension_results: list[AgentResult],
        data: ApplicationData,
    ) -> dict[str, Any]:
        """Apply intelligent lending strategy overrides to LLM output."""
        overall_score = parsed["overall_score"]

        # Extract key dimension scores
        dim_scores = {r.dimension_name: r.score for r in dimension_results if r.succeeded}
        fraud_score = dim_scores.get("fraud_risk", 0)
        compensating_score = dim_scores.get("compensating_factors", 50)
        stress_test_fails = self._check_stress_test(data)
        reserve_deficit = self._check_reserve_deficit(data)

        conditions = list(parsed.get("conditions", []))

        # Fraud override: high fraud score forces deny
        if fraud_score >= 60:
            parsed["recommendation"] = "deny"
            parsed["key_concerns"] = parsed.get("key_concerns", [])
            parsed["key_concerns"].insert(0, "Elevated fraud risk indicators detected")
            logger.info(
                f"Fraud override: fraud_score={fraud_score} -> deny "
                f"for {data.application_id}"
            )
            return parsed

        # Score-based recommendation with intelligent adjustments
        if overall_score >= 80:
            if stress_test_fails:
                parsed["recommendation"] = "conditional_approve"
                conditions.append("Rate lock and income verification required before closing")
                conditions.append("Escrow account required")
            else:
                parsed["recommendation"] = "approve"

        elif overall_score >= 60:
            has_recovery = self._detect_recovery_trajectory(dimension_results)
            if compensating_score >= 70 and has_recovery:
                parsed["recommendation"] = "conditional_approve"
                conditions.append("Employment verification within 10 days of closing")
                conditions.append("Additional documentation of income stability required")
            elif stress_test_fails or reserve_deficit:
                parsed["recommendation"] = "deny"
            else:
                parsed["recommendation"] = "review"

        elif overall_score >= 40:
            if compensating_score >= 75:
                parsed["recommendation"] = "review"
            else:
                parsed["recommendation"] = "deny"
        else:
            parsed["recommendation"] = "deny"

        parsed["conditions"] = conditions
        return parsed

    def _check_stress_test(self, data: ApplicationData) -> bool:
        """Simulate affordability under stress: 20% income drop or 2% rate rise."""
        if not data.dti_ratio or not data.loan_amount:
            return False

        employment = data.employment_info or {}
        annual_income = employment.get("annual_income", 0) or 0
        if annual_income <= 0:
            return False

        # Stressed income = 80% of current
        stressed_monthly_income = (annual_income * 0.80) / 12

        # Estimate mortgage payment with 2% rate increase
        rate = (data.base_interest_rate or 6.5) + 2.0
        monthly_rate = rate / 100 / 12
        term = (data.loan_term_months or 360)
        loan = float(data.loan_amount)

        if monthly_rate > 0 and term > 0:
            stressed_payment = loan * (
                monthly_rate * (1 + monthly_rate) ** term
            ) / ((1 + monthly_rate) ** term - 1)
        else:
            return False

        # Get total monthly debts
        monthly_debts = data.financial_info.get("monthly_debts", {})
        total_other_debts = sum(
            float(v) for v in monthly_debts.values()
            if isinstance(v, (int, float))
        )

        stressed_dti = (
            (stressed_payment + total_other_debts) / stressed_monthly_income * 100
            if stressed_monthly_income > 0
            else 100
        )

        return stressed_dti > 50

    def _check_reserve_deficit(self, data: ApplicationData) -> bool:
        """Check if borrower has less than 3 months of mortgage payments in reserves."""
        financial = data.financial_info or {}
        liquid_assets = financial.get("liquid_assets", 0) or 0
        down_payment = float(data.down_payment or 0)

        # Reserves after down payment
        reserves_after_dp = max(0, liquid_assets - down_payment)

        # Estimate monthly mortgage payment
        if data.loan_amount and data.base_interest_rate:
            rate = data.base_interest_rate / 100 / 12
            term = data.loan_term_months or 360
            loan = float(data.loan_amount)
            if rate > 0:
                monthly_payment = loan * (
                    rate * (1 + rate) ** term
                ) / ((1 + rate) ** term - 1)
            else:
                monthly_payment = loan / term
        else:
            return False

        return reserves_after_dp < (monthly_payment * 3)

    def _detect_recovery_trajectory(
        self,
        dimension_results: list[AgentResult],
    ) -> bool:
        """Detect if borrower shows a recovery trajectory from past credit events."""
        for r in dimension_results:
            all_factors = r.positive_factors + r.mitigating_factors
            for factor in all_factors:
                factor_lower = factor.lower()
                if any(keyword in factor_lower for keyword in [
                    "recovery", "improving", "rebuilt", "restored",
                    "clean recent", "on-time recent", "rehabilitated",
                ]):
                    return True
        return False

    def _rule_based_aggregation(
        self,
        dimension_results: list[AgentResult],
        data: ApplicationData,
        error: Exception | None = None,
    ) -> dict[str, Any]:
        """Fallback rule-based aggregation with intelligent logic."""
        total_weighted = sum(r.weighted_score for r in dimension_results if r.succeeded)
        total_weight = sum(r.weight for r in dimension_results if r.succeeded)
        overall = total_weighted / total_weight if total_weight > 0 else 50

        # Extract fraud score if available
        dim_scores = {r.dimension_name: r.score for r in dimension_results if r.succeeded}
        fraud_score = dim_scores.get("fraud_risk", 0)
        compensating_score = dim_scores.get("compensating_factors", 50)

        # Intelligent recommendation
        conditions: list[str] = []
        stress_test_fails = self._check_stress_test(data)

        if fraud_score >= 60:
            band, rec = "critical", "deny"
        elif overall >= 80:
            if stress_test_fails:
                band, rec = "low", "conditional_approve"
                conditions.append("Rate lock and income verification required")
            else:
                band, rec = "low", "approve"
        elif overall >= 60:
            band = "medium"
            if compensating_score >= 70:
                rec = "conditional_approve"
                conditions.append("Additional documentation required")
            elif stress_test_fails:
                rec = "deny"
            else:
                rec = "review"
        elif overall >= 40:
            band = "high"
            if compensating_score >= 75:
                rec = "review"
            else:
                rec = "deny"
        else:
            band, rec = "critical", "deny"

        all_risks = []
        all_positives = []
        for r in dimension_results:
            all_risks.extend(r.risk_factors[:2])
            all_positives.extend(r.positive_factors[:2])

        error_msg = f" (AI unavailable: {error})" if error else ""
        return {
            "overall_score": overall,
            "risk_band": band,
            "recommendation": rec,
            "summary": f"Rule-based assessment{error_msg}. Score: {overall:.1f}/100.",
            "key_strengths": all_positives[:5],
            "key_concerns": all_risks[:5],
            "conditions": conditions,
            "confidence": 0.5,
            "tokens_used": 0,
            "latency_ms": 0,
            "fallback": True,
        }

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        """Not used directly — use aggregate() instead."""
        return []
