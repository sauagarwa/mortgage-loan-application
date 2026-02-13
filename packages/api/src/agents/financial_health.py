"""
Financial Health Agent — evaluates DTI, assets, and overall financial position.
"""

from .base import ApplicationData, BaseAgent


class FinancialHealthAgent(BaseAgent):
    dimension_name = "financial_health"
    agent_name = "financial_health"
    weight = 0.15

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        financial = data.financial_info
        emp = data.employment_info

        monthly_debts = financial.get("monthly_debts", {})
        if isinstance(monthly_debts, dict):
            total_monthly_debt = sum(
                float(v) for v in monthly_debts.values()
                if isinstance(v, (int, float))
            )
            debt_breakdown = "\n".join(
                f"  - {k.replace('_', ' ').title()}: {self._format_currency(v)}"
                for k, v in monthly_debts.items()
                if isinstance(v, (int, float)) and v > 0
            )
        else:
            total_monthly_debt = 0
            debt_breakdown = "  Not provided"

        # Financial documents
        fin_docs = [
            d for d in data.documents
            if d["document_type"] in ("bank_statement", "tax_return", "proof_of_assets")
        ]
        doc_summary = ""
        if fin_docs:
            doc_lines = []
            for d in fin_docs:
                conf = d.get("extraction_confidence")
                conf_str = f" ({conf:.0%})" if conf else ""
                doc_lines.append(f"- {d['document_type']}: {d['status']}{conf_str}")
            doc_summary = "\n".join(doc_lines)
        else:
            doc_summary = "No financial documents uploaded"

        system_msg = f"""You are a mortgage financial health analyst AI. Evaluate the applicant's
overall financial position including debt-to-income ratio, assets, and reserves.

{self.RESULT_SCHEMA_INSTRUCTION}

Financial health scoring guidelines:
- DTI <= 28%: Excellent front-end ratio (85-100)
- DTI 28-36%: Good (70-84)
- DTI 36-43%: Acceptable for most programs (50-69)
- DTI 43-50%: High, may qualify with compensating factors (30-49)
- DTI > 50%: Very high risk (0-29)

Also consider:
- Liquid reserves (months of mortgage payments covered)
- Total assets relative to loan amount
- Savings patterns and financial stability"""

        annual_income = emp.get("annual_income", 0) or financial.get("annual_income", 0)
        monthly_income = annual_income / 12 if annual_income else 0

        user_msg = f"""Analyze this mortgage applicant's financial health:

**Income:**
- Annual Income: {self._format_currency(annual_income)}
- Monthly Income: {self._format_currency(monthly_income)}

**Monthly Debts:**
{debt_breakdown}
- Total Monthly Obligations: {self._format_currency(total_monthly_debt)}

**DTI Ratio:** {self._format_pct(data.dti_ratio)}

**Assets:**
- Total Assets: {self._format_currency(financial.get("total_assets"))}
- Liquid Assets: {self._format_currency(financial.get("liquid_assets"))}
- Retirement Accounts: {self._format_currency(financial.get("retirement_accounts"))}

**Loan Details:**
- Loan Amount: {self._format_currency(data.loan_amount)}
- Down Payment: {self._format_currency(data.down_payment)}

**Financial Documents:**
{doc_summary}

Provide your financial health assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
