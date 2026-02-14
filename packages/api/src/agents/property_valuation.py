"""
Property Valuation Agent — evaluates property and collateral risk.
"""

from .base import ApplicationData, BaseAgent


class PropertyValuationAgent(BaseAgent):
    dimension_name = "property"
    agent_name = "property_valuation"
    weight = 0.05

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        prop = data.property_info

        purchase_price = prop.get("purchase_price", 0)
        down_payment = data.down_payment or 0
        ltv = ((purchase_price - down_payment) / purchase_price * 100) if purchase_price else None

        # Property-related documents
        prop_docs = [
            d for d in data.documents
            if d["document_type"] in ("purchase_agreement",)
        ]
        doc_summary = ""
        if prop_docs:
            doc_lines = [f"- {d['document_type']}: {d['status']}" for d in prop_docs]
            doc_summary = "\n".join(doc_lines)
        else:
            doc_summary = "No property documents uploaded"

        system_msg = f"""You are a mortgage property risk analyst AI. Evaluate the property as collateral
and assess property-related risk factors.

{self.RESULT_SCHEMA_INSTRUCTION}

Property scoring guidelines:
- Single-family primary residence with LTV < 80%: 85-100
- Primary residence with LTV 80-90%: 70-84
- Primary residence with LTV 90-95%: 55-69
- Investment property or high LTV: 30-54
- Non-standard property types or very high LTV: 0-29

Property type risk (low to high):
Single Family < Townhouse < Condo < Multi-Family < Manufactured

Usage risk (low to high):
Primary Residence < Secondary Home < Investment Property"""

        user_msg = f"""Analyze this mortgage property:

**Property Details:**
- Type: {prop.get("property_type", "Not provided")}
- Usage: {prop.get("usage_type", prop.get("property_use", "Not provided"))}
- Address: {prop.get("address", "Not provided")}
- Year Built: {prop.get("year_built", "Not provided")}

**Financial:**
- Purchase Price: {self._format_currency(purchase_price)}
- Down Payment: {self._format_currency(down_payment)}
- Loan Amount: {self._format_currency(data.loan_amount)}
- Loan-to-Value (LTV): {self._format_pct(ltv)}

**PMI Required:** {"Yes" if ltv and ltv > 80 else "No" if ltv else "Unknown"}

**Property Documents:**
{doc_summary}

**Loan Product:** {data.loan_product_name or "N/A"} ({data.loan_product_type or "N/A"})

Provide your property risk assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
