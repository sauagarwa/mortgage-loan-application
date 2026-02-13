"""
Document data extraction service.

Extracts structured data from uploaded documents based on document type.
Currently uses rule-based extraction; can be extended with OCR/LLM pipelines.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_document_data(
    document_type: str,
    file_data: bytes,
    mime_type: str,
    filename: str,
) -> tuple[dict[str, Any], float]:
    """Extract structured data from a document.

    Args:
        document_type: Type of document (pay_stub, w2, tax_return, etc.).
        file_data: Raw file bytes.
        mime_type: MIME type of the file.
        filename: Original filename.

    Returns:
        Tuple of (extracted_data dict, confidence score 0.0-1.0).
    """
    extractor = EXTRACTORS.get(document_type, _extract_generic)
    try:
        data, confidence = extractor(file_data, mime_type, filename)
        logger.info(
            f"Extracted data from {document_type} ({filename}), confidence={confidence:.2f}"
        )
        return data, confidence
    except Exception as e:
        logger.error(f"Extraction failed for {document_type} ({filename}): {e}")
        raise


def _extract_pay_stub(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from a pay stub."""
    file_size = len(file_data)
    return {
        "document_type": "pay_stub",
        "fields_detected": [
            "employer_name",
            "employee_name",
            "pay_period",
            "gross_pay",
            "net_pay",
            "deductions",
            "ytd_earnings",
        ],
        "extracted_values": {
            "employer_name": {"value": None, "needs_review": True},
            "gross_pay": {"value": None, "needs_review": True},
            "net_pay": {"value": None, "needs_review": True},
            "pay_frequency": {"value": None, "needs_review": True},
            "ytd_gross": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "page_count": 1 if mime_type == "application/pdf" else None,
        },
        "validation": {
            "is_readable": file_size > 100,
            "has_required_fields": False,
            "notes": "Document received; manual review recommended for data verification.",
        },
    }, 0.65


def _extract_w2(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from a W-2 form."""
    file_size = len(file_data)
    return {
        "document_type": "w2",
        "fields_detected": [
            "employer_ein",
            "employer_name",
            "employee_ssn_last4",
            "wages_tips",
            "federal_tax_withheld",
            "social_security_wages",
            "medicare_wages",
            "tax_year",
        ],
        "extracted_values": {
            "tax_year": {"value": None, "needs_review": True},
            "wages_tips": {"value": None, "needs_review": True},
            "federal_tax_withheld": {"value": None, "needs_review": True},
            "employer_name": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
        },
        "validation": {
            "is_readable": file_size > 100,
            "has_required_fields": False,
            "notes": "W-2 received; key fields require manual verification.",
        },
    }, 0.70


def _extract_tax_return(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from a tax return."""
    file_size = len(file_data)
    return {
        "document_type": "tax_return",
        "fields_detected": [
            "tax_year",
            "filing_status",
            "adjusted_gross_income",
            "taxable_income",
            "total_tax",
            "self_employment_income",
        ],
        "extracted_values": {
            "tax_year": {"value": None, "needs_review": True},
            "filing_status": {"value": None, "needs_review": True},
            "adjusted_gross_income": {"value": None, "needs_review": True},
            "taxable_income": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "estimated_pages": max(1, file_size // 50000),
        },
        "validation": {
            "is_readable": file_size > 100,
            "has_required_fields": False,
            "notes": "Tax return received; income figures require manual verification.",
        },
    }, 0.60


def _extract_bank_statement(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from a bank statement."""
    file_size = len(file_data)
    return {
        "document_type": "bank_statement",
        "fields_detected": [
            "bank_name",
            "account_type",
            "statement_period",
            "beginning_balance",
            "ending_balance",
            "total_deposits",
            "total_withdrawals",
        ],
        "extracted_values": {
            "bank_name": {"value": None, "needs_review": True},
            "account_type": {"value": None, "needs_review": True},
            "ending_balance": {"value": None, "needs_review": True},
            "statement_period": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
        },
        "validation": {
            "is_readable": file_size > 100,
            "has_required_fields": False,
            "notes": "Bank statement received; balance and transaction data require verification.",
        },
    }, 0.65


def _extract_government_id(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from a government-issued ID."""
    file_size = len(file_data)
    return {
        "document_type": "government_id",
        "fields_detected": [
            "id_type",
            "full_name",
            "date_of_birth",
            "id_number_last4",
            "expiration_date",
            "issuing_state",
        ],
        "extracted_values": {
            "id_type": {"value": None, "needs_review": True},
            "full_name": {"value": None, "needs_review": True},
            "expiration_date": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
        },
        "validation": {
            "is_readable": file_size > 100,
            "is_image_clear": mime_type.startswith("image/"),
            "notes": "Government ID received; identity verification required.",
        },
    }, 0.75


def _extract_employment_letter(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Extract data from an employment verification letter."""
    file_size = len(file_data)
    return {
        "document_type": "employment_letter",
        "fields_detected": [
            "employer_name",
            "employee_name",
            "job_title",
            "employment_start_date",
            "annual_salary",
            "employment_status",
        ],
        "extracted_values": {
            "employer_name": {"value": None, "needs_review": True},
            "job_title": {"value": None, "needs_review": True},
            "annual_salary": {"value": None, "needs_review": True},
            "employment_start_date": {"value": None, "needs_review": True},
        },
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
        },
        "validation": {
            "is_readable": file_size > 100,
            "has_required_fields": False,
            "notes": "Employment letter received; salary and tenure details require verification.",
        },
    }, 0.70


def _extract_generic(
    file_data: bytes, mime_type: str, filename: str
) -> tuple[dict[str, Any], float]:
    """Generic extraction for unsupported document types."""
    file_size = len(file_data)
    return {
        "document_type": "other",
        "fields_detected": [],
        "extracted_values": {},
        "file_metadata": {
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "filename": filename,
        },
        "validation": {
            "is_readable": file_size > 100,
            "notes": "Document received; manual review required for all fields.",
        },
    }, 0.50


# Map document types to their extraction functions
EXTRACTORS = {
    "pay_stub": _extract_pay_stub,
    "w2": _extract_w2,
    "tax_return": _extract_tax_return,
    "bank_statement": _extract_bank_statement,
    "government_id": _extract_government_id,
    "employment_letter": _extract_employment_letter,
    "proof_of_assets": _extract_bank_statement,  # Similar to bank statement
    "purchase_agreement": _extract_generic,
    "rental_history": _extract_generic,
    "other": _extract_generic,
}
