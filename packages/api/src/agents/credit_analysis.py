"""
Credit Analysis Agent — evaluates applicant credit profile risk.
"""

from .base import ApplicationData, BaseAgent


class CreditAnalysisAgent(BaseAgent):
    dimension_name = "credit_history"
    agent_name = "credit_analysis"
    weight = 0.12

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        financial = data.financial_info
        declarations = data.declarations

        credit_score = financial.get("credit_score", "Not provided")
        has_bankruptcy = declarations.get("has_bankruptcy", False)
        bankruptcy_details = declarations.get("bankruptcy_details", "")
        has_foreclosure = declarations.get("has_foreclosure", False)
        has_judgments = declarations.get("has_judgments", False)
        has_delinquent_debt = declarations.get("has_delinquent_debt", False)

        # Bureau data enrichment
        bureau_section = ""
        if data.credit_report:
            cr = data.credit_report
            bureau_score = cr.get("credit_score", "N/A")
            utilization = cr.get("credit_utilization", "N/A")
            on_time_pct = cr.get("on_time_payments_pct", "N/A")
            total_accounts = cr.get("total_accounts", "N/A")
            open_accounts = cr.get("open_accounts", "N/A")
            oldest_months = cr.get("oldest_account_months", 0)
            avg_age_months = cr.get("avg_account_age_months", 0)
            late_30 = cr.get("late_payments_30d", 0)
            late_60 = cr.get("late_payments_60d", 0)
            late_90 = cr.get("late_payments_90d", 0)
            num_tradelines = len(cr.get("tradelines", []))
            num_public_records = len(cr.get("public_records", []))
            score_factors = cr.get("score_factors", [])

            bureau_section = f"""
**Credit Bureau Report (FICO 8):**
- Bureau Score: {bureau_score}
- Credit Utilization: {utilization}%
- On-Time Payments: {on_time_pct}%
- Late Payments (30/60/90+ days): {late_30}/{late_60}/{late_90}
- Total Accounts: {total_accounts} ({open_accounts} open)
- Tradelines: {num_tradelines}
- Oldest Account: {oldest_months // 12} years {oldest_months % 12} months
- Average Account Age: {avg_age_months // 12} years {avg_age_months % 12} months
- Public Records: {num_public_records}
- Score Factors: {'; '.join(score_factors[:4]) if score_factors else 'N/A'}
"""

        system_msg = f"""You are a mortgage credit risk analyst AI. Analyze the applicant's credit profile
and provide a risk score from 0-100 with detailed factors.

{self.RESULT_SCHEMA_INSTRUCTION}

Credit scoring guidelines:
- 760+ credit score: Excellent (85-100 points)
- 700-759: Good (70-84 points)
- 660-699: Fair (55-69 points)
- 620-659: Below average (35-54 points)
- Below 620: Poor (0-34 points)

Important: When bureau data is available, use the bureau score as the primary indicator
rather than the self-reported score. Consider utilization, payment history, and account
age as additional factors. A borrower with past derogatory marks but clean recent
history (24+ months of on-time payments) may deserve recency-adjusted scoring."""

        user_msg = f"""Analyze this mortgage applicant's credit profile:

**Self-Reported Credit Score:** {credit_score}
**Bankruptcy History:** {"Yes" if has_bankruptcy else "No"}
{f"Bankruptcy Details: {bankruptcy_details}" if has_bankruptcy and bankruptcy_details else ""}
**Foreclosure History:** {"Yes" if has_foreclosure else "No"}
**Outstanding Judgments:** {"Yes" if has_judgments else "No"}
**Delinquent Federal Debt:** {"Yes" if has_delinquent_debt else "No"}
{bureau_section}
**Loan Details:**
- Loan Amount: {self._format_currency(data.loan_amount)}
- Loan Product: {data.loan_product_name or "N/A"} ({data.loan_product_type or "N/A"})

Provide your credit risk assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
