"""
Risk assessment pipeline orchestrator.

Runs all dimension agents (in parallel where possible) and aggregates results.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from .base import AgentResult, ApplicationData, BaseAgent
from .credit_analysis import CreditAnalysisAgent
from .employment_verification import EmploymentVerificationAgent
from .financial_health import FinancialHealthAgent
from .property_valuation import PropertyValuationAgent
from .applicant_profile import ApplicantProfileAgent
from .regulatory_compliance import RegulatoryComplianceAgent
from .document_analysis import DocumentAnalysisAgent
from .risk_aggregation import RiskAggregationAgent

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Full pipeline execution result."""

    overall_score: float
    risk_band: str
    recommendation: str
    summary: str
    confidence: float
    conditions: list[dict[str, Any]]
    dimension_results: list[AgentResult]
    aggregation_result: dict[str, Any]
    total_tokens: int = 0
    total_processing_time_ms: int = 0
    agents_succeeded: int = 0
    agents_failed: int = 0


# Default dimension agents in execution order
DEFAULT_AGENTS: list[type[BaseAgent]] = [
    CreditAnalysisAgent,
    EmploymentVerificationAgent,
    FinancialHealthAgent,
    PropertyValuationAgent,
    ApplicantProfileAgent,
    RegulatoryComplianceAgent,
    DocumentAnalysisAgent,
]


def run_pipeline(
    data: ApplicationData,
    agents: list[type[BaseAgent]] | None = None,
    max_parallel: int = 4,
    use_llm: bool = True,
) -> PipelineResult:
    """Run the full risk assessment pipeline.

    Args:
        data: Application data to analyze.
        agents: List of agent classes to run (defaults to all).
        max_parallel: Maximum parallel agent executions.
        use_llm: If False, uses rule-based fallback for all agents.

    Returns:
        PipelineResult with all scores and aggregated assessment.
    """
    start = time.time()
    agent_classes = agents or DEFAULT_AGENTS

    logger.info(
        f"Starting risk pipeline for {data.application_id} "
        f"with {len(agent_classes)} agents"
    )

    # Instantiate agents
    agent_instances = [cls() for cls in agent_classes]

    # Run dimension agents in parallel
    dimension_results: list[AgentResult] = []

    if use_llm:
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_agent = {
                executor.submit(agent.analyze, data): agent
                for agent in agent_instances
            }

            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    dimension_results.append(result)
                except Exception as e:
                    logger.error(f"Agent {agent.agent_name} crashed: {e}")
                    dimension_results.append(AgentResult(
                        dimension_name=agent.dimension_name,
                        agent_name=agent.agent_name,
                        score=50.0,
                        weight=agent.weight,
                        risk_factors=["Agent execution failed"],
                        explanation=f"Agent crashed: {str(e)[:200]}",
                        error=str(e)[:500],
                    ))
    else:
        # Rule-based fallback — use the existing rule engine
        from ..worker.tasks.risk_assessment import DIMENSION_SCORERS, DIMENSION_WEIGHTS
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        from ..worker.db import get_sync_session
        from db import Application

        with get_sync_session() as session:
            result = session.execute(
                select(Application)
                .options(joinedload(Application.documents), joinedload(Application.loan_product))
                .where(Application.id == data.application_id)
            )
            application = result.unique().scalar_one_or_none()

            if application:
                for dim_name, scorer in DIMENSION_SCORERS.items():
                    try:
                        scored = scorer(application)
                        weight = DIMENSION_WEIGHTS.get(dim_name, 0.1)
                        dimension_results.append(AgentResult(
                            dimension_name=dim_name,
                            agent_name="rule_engine",
                            score=scored["score"],
                            weight=weight,
                            positive_factors=scored.get("positive_factors", []),
                            risk_factors=scored.get("risk_factors", []),
                            mitigating_factors=scored.get("mitigating_factors", []),
                            explanation=scored.get("explanation", ""),
                        ))
                    except Exception as e:
                        dimension_results.append(AgentResult(
                            dimension_name=dim_name,
                            agent_name="rule_engine",
                            score=50.0,
                            weight=DIMENSION_WEIGHTS.get(dim_name, 0.1),
                            error=str(e),
                        ))

    # Sort results by dimension name for consistency
    dimension_results.sort(key=lambda r: r.dimension_name)

    # Count successes/failures
    succeeded = sum(1 for r in dimension_results if r.succeeded)
    failed = sum(1 for r in dimension_results if not r.succeeded)
    total_tokens = sum(r.tokens_used for r in dimension_results)

    logger.info(
        f"Dimension analysis complete: {succeeded} succeeded, {failed} failed, "
        f"total tokens: {total_tokens}"
    )

    # Run aggregation
    aggregator = RiskAggregationAgent()
    if use_llm:
        aggregation_result = aggregator.aggregate(data, dimension_results)
    else:
        # Simple weighted average fallback
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

        aggregation_result = {
            "overall_score": overall,
            "risk_band": band,
            "recommendation": rec,
            "summary": f"Rule-based assessment. Weighted score: {overall:.1f}/100.",
            "key_strengths": all_positives[:5],
            "key_concerns": all_risks[:5],
            "conditions": [],
            "confidence": 0.6,
        }

    total_tokens += aggregation_result.get("tokens_used", 0)
    total_time = int((time.time() - start) * 1000)

    # Build conditions list
    conditions = [
        {"condition": c, "status": "pending"}
        for c in aggregation_result.get("conditions", [])
    ]

    result = PipelineResult(
        overall_score=aggregation_result["overall_score"],
        risk_band=aggregation_result["risk_band"],
        recommendation=aggregation_result["recommendation"],
        summary=aggregation_result.get("summary", ""),
        confidence=aggregation_result.get("confidence", 0.5),
        conditions=conditions,
        dimension_results=dimension_results,
        aggregation_result=aggregation_result,
        total_tokens=total_tokens,
        total_processing_time_ms=total_time,
        agents_succeeded=succeeded,
        agents_failed=failed,
    )

    logger.info(
        f"Pipeline complete for {data.application_id}: "
        f"score={result.overall_score:.1f}, band={result.risk_band}, "
        f"rec={result.recommendation}, tokens={total_tokens}, time={total_time}ms"
    )

    return result
