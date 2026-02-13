"""
Document Analysis Agent — evaluates document completeness and data quality.
"""

from .base import ApplicationData, BaseAgent


class DocumentAnalysisAgent(BaseAgent):
    dimension_name = "document_quality"
    agent_name = "document_analysis"
    weight = 0.10

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        # Categorize documents
        uploaded = []
        processed = []
        errors = []
        for d in data.documents:
            entry = {
                "type": d["document_type"],
                "status": d["status"],
                "confidence": d.get("extraction_confidence"),
                "extracted": d.get("extracted_data"),
            }
            if d["status"] == "processed":
                processed.append(entry)
            elif d["status"] == "error":
                errors.append(entry)
            uploaded.append(entry)

        # Build document inventory
        doc_inventory = []
        for d in uploaded:
            conf = f" | confidence: {d['confidence']:.0%}" if d["confidence"] else ""
            doc_inventory.append(f"- {d['type']}: {d['status']}{conf}")

        all_types = {
            "government_id", "pay_stub", "w2", "tax_return",
            "bank_statement", "employment_letter", "proof_of_assets",
            "purchase_agreement",
        }
        uploaded_types = {d["type"] for d in uploaded}
        missing = all_types - uploaded_types

        # Extracted data quality
        extraction_details = []
        for d in processed:
            ext = d.get("extracted") or {}
            validation = ext.get("validation", {})
            fields = ext.get("fields_detected", [])
            extraction_details.append(
                f"- {d['type']}: {len(fields)} fields detected, "
                f"readable={validation.get('is_readable', 'unknown')}"
            )

        system_msg = f"""You are a mortgage document quality analyst AI. Evaluate the completeness,
quality, and reliability of the documentation provided with this application.

{self.RESULT_SCHEMA_INSTRUCTION}

Document quality scoring:
- All key documents present and processed with high confidence: 85-100
- Most documents present, good extraction quality: 70-84
- Some important documents missing or low quality: 50-69
- Many documents missing or processing errors: 30-49
- Critical documents missing, unable to verify: 0-29

Key documents for mortgage applications:
1. Government ID (required for identity verification)
2. Pay stubs (required for income verification)
3. W-2 forms (required for income history)
4. Tax returns (required for self-employed or complex income)
5. Bank statements (required for asset verification)
6. Employment letter (supporting document)
7. Purchase agreement (required for purchase transactions)"""

        user_msg = f"""Analyze the document package for this mortgage application:

**Document Inventory ({len(uploaded)} total):**
{chr(10).join(doc_inventory) if doc_inventory else "No documents uploaded"}

**Missing Document Types:**
{", ".join(sorted(missing)) if missing else "None - all standard types present"}

**Processing Results:**
- Successfully processed: {len(processed)}
- Processing errors: {len(errors)}
- Pending/uploaded: {len(uploaded) - len(processed) - len(errors)}

**Extraction Quality:**
{chr(10).join(extraction_details) if extraction_details else "No documents processed yet"}

**Application Context:**
- Application Status: {data.status}
- Employment Type: {data.employment_info.get("employment_status", "N/A")}
  (self-employed applicants need additional documentation like tax returns)

Provide your document quality assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
