"""
Regulatory Compliance Agent — checks for regulatory red flags and compliance issues.
"""

from .base import ApplicationData, BaseAgent


class RegulatoryComplianceAgent(BaseAgent):
    dimension_name = "regulatory_compliance"
    agent_name = "regulatory_compliance"
    weight = 0.10

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        declarations = data.declarations
        financial = data.financial_info
        prop = data.property_info

        # Check document completeness
        doc_types_uploaded = {d["document_type"] for d in data.documents}
        required_docs = {"government_id", "pay_stub"}
        recommended_docs = {"w2", "tax_return", "bank_statement"}
        missing_required = required_docs - doc_types_uploaded
        missing_recommended = recommended_docs - doc_types_uploaded

        system_msg = f"""You are a mortgage regulatory compliance analyst AI. Check the application
for regulatory requirements, documentation completeness, and compliance flags.

{self.RESULT_SCHEMA_INSTRUCTION}

Regulatory compliance scoring:
- All required docs present, no regulatory flags: 85-100
- Minor documentation gaps, no compliance issues: 70-84
- Some documentation missing, minor compliance concerns: 50-69
- Significant documentation gaps or compliance flags: 30-49
- Major regulatory issues or incomplete application: 0-29

Key regulations to consider:
- TILA (Truth in Lending Act): proper disclosure requirements
- RESPA: real estate settlement procedures
- ECOA: equal credit opportunity (no discrimination)
- HMDA: home mortgage disclosure requirements
- QM rules: qualified mortgage standards (DTI limits, points/fees)
- BSA/AML: anti-money laundering red flags
- Ability-to-Repay rule: borrower must demonstrate repayment ability"""

        user_msg = f"""Check this mortgage application for regulatory compliance:

**Documentation Status:**
- Required documents missing: {", ".join(missing_required) if missing_required else "None"}
- Recommended documents missing: {", ".join(missing_recommended) if missing_recommended else "None"}
- Total documents uploaded: {len(data.documents)}
- Documents processed: {sum(1 for d in data.documents if d["status"] == "processed")}

**Declarations & Compliance Flags:**
- Bankruptcy history: {declarations.get("has_bankruptcy", False)}
- Foreclosure history: {declarations.get("has_foreclosure", False)}
- Outstanding judgments: {declarations.get("has_judgments", False)}
- Delinquent federal debt: {declarations.get("has_delinquent_debt", False)}
- Party to lawsuit: {declarations.get("is_party_to_lawsuit", False)}
- Alimony/child support obligation: {declarations.get("has_alimony_obligation", False)}
- Co-signer on other loans: {declarations.get("is_cosigner", False)}

**QM Qualification Check:**
- DTI Ratio: {self._format_pct(data.dti_ratio)} (QM limit: 43%)
- Loan Type: {data.loan_product_type or "N/A"}
- Loan Amount: {self._format_currency(data.loan_amount)}

**Property:**
- Usage: {prop.get("usage_type", prop.get("property_use", "N/A"))}
- Type: {prop.get("property_type", "N/A")}

**Income Verification:**
- Annual Income Reported: {self._format_currency(financial.get("annual_income"))}
- Income documents uploaded: {sum(1 for d in data.documents if d["document_type"] in ("pay_stub", "w2", "tax_return", "employment_letter"))}

Provide your regulatory compliance assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
