"""
Employment Verification Agent — evaluates employment stability and income.
"""

from .base import ApplicationData, BaseAgent


class EmploymentVerificationAgent(BaseAgent):
    dimension_name = "employment"
    agent_name = "employment_verification"
    weight = 0.05

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        emp = data.employment_info
        financial = data.financial_info

        # Find employment-related documents
        emp_docs = [
            d for d in data.documents
            if d["document_type"] in ("pay_stub", "w2", "employment_letter")
        ]
        doc_summary = ""
        if emp_docs:
            doc_lines = []
            for d in emp_docs:
                status = d["status"]
                confidence = d.get("extraction_confidence")
                conf_str = f" (confidence: {confidence:.0%})" if confidence else ""
                doc_lines.append(f"- {d['document_type']}: {status}{conf_str}")
            doc_summary = "\n".join(doc_lines)
        else:
            doc_summary = "No employment documents uploaded"

        system_msg = f"""You are a mortgage employment verification analyst AI. Evaluate the stability
and reliability of the applicant's employment and income.

{self.RESULT_SCHEMA_INSTRUCTION}

Employment scoring guidelines:
- Stable full-time employment 5+ years at same employer: 85-100
- Full-time employment 2-5 years: 70-84
- Full-time employment < 2 years: 55-69
- Self-employed with 2+ years history: 60-80
- Self-employed < 2 years: 35-55
- Unemployed or gaps in employment: 0-40

Consider income-to-loan ratio: higher income relative to loan = lower risk.
Verified income (via documents) is more reliable than self-reported."""

        user_msg = f"""Analyze this mortgage applicant's employment profile:

**Employment Status:** {emp.get("employment_status", "Not provided")}
**Employer:** {emp.get("employer_name", "Not provided")}
**Job Title:** {emp.get("job_title", "Not provided")}
**Years at Current Job:** {emp.get("years_at_job", "Not provided")}
**Annual Income:** {self._format_currency(emp.get("annual_income") or financial.get("annual_income"))}
**Previous Employer:** {emp.get("previous_employer", "Not provided")}

**Supporting Documents:**
{doc_summary}

**Loan Context:**
- Loan Amount: {self._format_currency(data.loan_amount)}
- Income-to-Loan Ratio: {self._format_pct((emp.get("annual_income", 0) / data.loan_amount * 100) if data.loan_amount and emp.get("annual_income") else None)}

Provide your employment risk assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
