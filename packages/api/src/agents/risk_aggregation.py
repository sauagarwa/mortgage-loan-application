"""
Risk Aggregation Agent — combines dimension scores into final assessment.

Uses LLM to synthesize individual agent results into a cohesive
risk summary with overall recommendation.
"""

from typing import Any

from .base import AgentResult, ApplicationData, BaseAgent


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
  "recommendation": "<approve|review|deny>",
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
- low risk (80+): "approve"
- medium risk (60-79): "review" (conditional approval may be appropriate)
- high risk (40-59): "review" (significant concerns need human judgment)
- critical risk (below 40): "deny"

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
high DTI is worse than either alone. Also consider any compensating factors."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    def aggregate(
        self,
        data: ApplicationData,
        dimension_results: list[AgentResult],
    ) -> dict[str, Any]:
        """Run aggregation analysis using LLM.

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

            # Validate recommendation
            valid_recs = {"approve", "review", "deny"}
            if parsed.get("recommendation") not in valid_recs:
                parsed["recommendation"] = "review"

            parsed["tokens_used"] = llm_response.total_tokens
            parsed["latency_ms"] = llm_response.latency_ms

            return parsed

        except Exception as e:
            # Fallback to rule-based aggregation
            total_weighted = sum(r.weighted_score for r in dimension_results if r.succeeded)
            total_weight = sum(r.weight for r in dimension_results if r.succeeded)
            overall = total_weighted / total_weight if total_weight > 0 else 50

            if overall >= 80:
                band, rec = "low", "approve"
            elif overall >= 60:
                band, rec = "medium", "review"
            elif overall >= 40:
                band, rec = "high", "review"
            else:
                band, rec = "critical", "deny"

            all_risks = []
            all_positives = []
            for r in dimension_results:
                all_risks.extend(r.risk_factors[:2])
                all_positives.extend(r.positive_factors[:2])

            return {
                "overall_score": overall,
                "risk_band": band,
                "recommendation": rec,
                "summary": f"Rule-based assessment (AI unavailable: {e}). Score: {overall:.1f}/100.",
                "key_strengths": all_positives[:5],
                "key_concerns": all_risks[:5],
                "conditions": [],
                "confidence": 0.5,
                "tokens_used": 0,
                "latency_ms": 0,
                "fallback": True,
            }

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        """Not used directly — use aggregate() instead."""
        return []
