"""
Credit Analysis Agent — evaluates applicant credit profile risk.
"""

from .base import ApplicationData, BaseAgent


class CreditAnalysisAgent(BaseAgent):
    dimension_name = "credit_history"
    agent_name = "credit_analysis"
    weight = 0.20

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        financial = data.financial_info
        declarations = data.declarations

        credit_score = financial.get("credit_score", "Not provided")
        has_bankruptcy = declarations.get("has_bankruptcy", False)
        bankruptcy_details = declarations.get("bankruptcy_details", "")
        has_foreclosure = declarations.get("has_foreclosure", False)
        has_judgments = declarations.get("has_judgments", False)
        has_delinquent_debt = declarations.get("has_delinquent_debt", False)

        system_msg = f"""You are a mortgage credit risk analyst AI. Analyze the applicant's credit profile
and provide a risk score from 0-100 with detailed factors.

{self.RESULT_SCHEMA_INSTRUCTION}

Credit scoring guidelines:
- 760+ credit score: Excellent (85-100 points)
- 700-759: Good (70-84 points)
- 660-699: Fair (55-69 points)
- 620-659: Below average (35-54 points)
- Below 620: Poor (0-34 points)

Derogatory marks (bankruptcy, foreclosure, judgments) should significantly reduce the score.
Each bankruptcy reduces score by 15-25 points, foreclosure by 20-30 points."""

        user_msg = f"""Analyze this mortgage applicant's credit profile:

**Credit Score:** {credit_score}
**Bankruptcy History:** {"Yes" if has_bankruptcy else "No"}
{f"Bankruptcy Details: {bankruptcy_details}" if has_bankruptcy and bankruptcy_details else ""}
**Foreclosure History:** {"Yes" if has_foreclosure else "No"}
**Outstanding Judgments:** {"Yes" if has_judgments else "No"}
**Delinquent Federal Debt:** {"Yes" if has_delinquent_debt else "No"}

**Loan Details:**
- Loan Amount: {self._format_currency(data.loan_amount)}
- Loan Product: {data.loan_product_name or "N/A"} ({data.loan_product_type or "N/A"})

Provide your credit risk assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
