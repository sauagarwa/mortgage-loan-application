"""
Base agent class for risk assessment dimension agents.

Each agent analyzes a specific dimension of a mortgage application
and returns a structured score with factors and explanation.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ..services.llm_gateway import LLMResponse, call_llm_json

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Standardized result from a dimension agent."""

    dimension_name: str
    agent_name: str
    score: float  # 0-100
    weight: float  # 0.0-1.0
    positive_factors: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    mitigating_factors: list[str] = field(default_factory=list)
    explanation: str = ""
    raw_llm_output: dict[str, Any] | None = None
    tokens_used: int = 0
    processing_time_ms: int = 0
    error: str | None = None

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass
class ApplicationData:
    """Flattened application data passed to agents for analysis."""

    application_id: str
    application_number: str
    status: str

    # Applicant info
    personal_info: dict[str, Any]
    employment_info: dict[str, Any]
    financial_info: dict[str, Any]
    property_info: dict[str, Any]
    declarations: dict[str, Any]

    # Computed fields
    loan_amount: float | None = None
    down_payment: float | None = None
    dti_ratio: float | None = None

    # Loan product
    loan_product_name: str | None = None
    loan_product_type: str | None = None
    loan_term_months: int | None = None
    base_interest_rate: float | None = None

    # Documents
    documents: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_orm(cls, application, documents=None) -> "ApplicationData":
        """Build from SQLAlchemy Application model."""
        loan_product = application.loan_product

        doc_list = []
        for doc in (documents or application.documents or []):
            doc_list.append({
                "document_type": doc.document_type,
                "status": doc.status,
                "extracted_data": doc.extracted_data,
                "extraction_confidence": (
                    float(doc.extraction_confidence) if doc.extraction_confidence else None
                ),
            })

        return cls(
            application_id=str(application.id),
            application_number=application.application_number,
            status=application.status,
            personal_info=application.personal_info or {},
            employment_info=application.employment_info or {},
            financial_info=application.financial_info or {},
            property_info=application.property_info or {},
            declarations=application.declarations or {},
            loan_amount=float(application.loan_amount) if application.loan_amount else None,
            down_payment=float(application.down_payment) if application.down_payment else None,
            dti_ratio=float(application.dti_ratio) if application.dti_ratio else None,
            loan_product_name=loan_product.name if loan_product else None,
            loan_product_type=loan_product.type if loan_product else None,
            loan_term_months=loan_product.term_months if loan_product else None,
            base_interest_rate=(
                float(loan_product.interest_rate) if loan_product and loan_product.interest_rate else None
            ),
            documents=doc_list,
        )


class BaseAgent:
    """Base class for risk assessment dimension agents.

    Subclasses must implement:
        - dimension_name: str
        - agent_name: str
        - weight: float
        - build_prompt(data: ApplicationData) -> list[dict]
        - parse_result(llm_output: dict, data: ApplicationData) -> AgentResult
    """

    dimension_name: str = "base"
    agent_name: str = "base_agent"
    weight: float = 0.1

    # LLM settings (can be overridden per agent)
    temperature: float = 0.1
    max_tokens: int = 2048
    provider: str | None = None  # None = use default

    # JSON schema instruction appended to system prompt
    RESULT_SCHEMA_INSTRUCTION = """
You must respond with valid JSON matching this schema:
{
  "score": <number 0-100>,
  "positive_factors": [<list of strings>],
  "risk_factors": [<list of strings>],
  "mitigating_factors": [<list of strings>],
  "explanation": "<string summarizing your analysis>"
}

Scoring guide:
- 90-100: Excellent, minimal risk
- 70-89: Good, low risk
- 50-69: Moderate, some concerns
- 30-49: Poor, significant risk factors
- 0-29: Very poor, major risk flags

Be specific and quantitative in your factors. Reference actual data values.
"""

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        """Build the LLM prompt messages for this agent.

        Must return messages in OpenAI chat format: [{role, content}].
        """
        raise NotImplementedError

    def parse_result(
        self, llm_output: dict[str, Any], data: ApplicationData
    ) -> AgentResult:
        """Parse LLM JSON output into an AgentResult.

        Default implementation handles the standard result schema.
        Override for custom parsing.
        """
        score = float(llm_output.get("score", 50))
        score = max(0, min(100, score))  # Clamp to 0-100

        return AgentResult(
            dimension_name=self.dimension_name,
            agent_name=self.agent_name,
            score=score,
            weight=self.weight,
            positive_factors=llm_output.get("positive_factors", []),
            risk_factors=llm_output.get("risk_factors", []),
            mitigating_factors=llm_output.get("mitigating_factors", []),
            explanation=llm_output.get("explanation", ""),
            raw_llm_output=llm_output,
        )

    def analyze(self, data: ApplicationData) -> AgentResult:
        """Run analysis on application data.

        Builds prompt, calls LLM, parses result. Handles errors gracefully.

        Args:
            data: Application data to analyze.

        Returns:
            AgentResult with score and factors.
        """
        start = time.time()
        logger.info(
            f"Agent {self.agent_name} starting analysis for {data.application_id}"
        )

        try:
            messages = self.build_prompt(data)
            llm_output, llm_response = call_llm_json(
                messages=messages,
                provider_name=self.provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = self.parse_result(llm_output, data)
            result.tokens_used = llm_response.total_tokens
            result.processing_time_ms = int((time.time() - start) * 1000)

            logger.info(
                f"Agent {self.agent_name} completed: score={result.score:.1f}, "
                f"tokens={result.tokens_used}, time={result.processing_time_ms}ms"
            )
            return result

        except Exception as e:
            processing_time = int((time.time() - start) * 1000)
            logger.error(
                f"Agent {self.agent_name} failed for {data.application_id}: {e}"
            )
            return AgentResult(
                dimension_name=self.dimension_name,
                agent_name=self.agent_name,
                score=50.0,  # Neutral fallback score
                weight=self.weight,
                risk_factors=[f"AI analysis unavailable: agent error"],
                explanation=f"Agent {self.agent_name} encountered an error. Using neutral score.",
                error=str(e)[:500],
                processing_time_ms=processing_time,
            )

    def _format_currency(self, amount: float | int | None) -> str:
        """Format a number as USD currency string."""
        if amount is None:
            return "N/A"
        return f"${amount:,.2f}"

    def _format_pct(self, value: float | None) -> str:
        """Format a number as percentage string."""
        if value is None:
            return "N/A"
        return f"{value:.1f}%"
