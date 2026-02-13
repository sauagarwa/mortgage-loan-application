# MortgageAI: API Specification

**Version:** 1.0
**Date:** 2026-02-13
**Base URL:** `/api/v1`

---

## 1. Overview

The MortgageAI API is a RESTful service built with FastAPI. All endpoints require authentication via Keycloak JWT tokens unless otherwise noted. Responses follow standard HTTP status codes and return JSON payloads.

### Common Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Standard Error Response

```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-02-13T10:30:00Z"
}
```

### Pagination

List endpoints support cursor-based pagination:

```
GET /api/v1/applications?limit=20&offset=0&sort_by=created_at&sort_order=desc
```

Response includes:
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

---

## 2. Authentication Endpoints

### 2.1 Keycloak Configuration

```
GET /api/v1/auth/config
```

**Auth Required:** No

**Description:** Returns Keycloak realm configuration for frontend initialization.

**Response 200:**
```json
{
  "realm": "mortgage-ai",
  "auth_server_url": "https://keycloak.example.com/auth",
  "client_id": "mortgage-ai-ui",
  "ssl_required": "external"
}
```

### 2.2 Current User Profile

```
GET /api/v1/auth/me
```

**Auth Required:** Yes (any role)

**Description:** Returns the authenticated user's profile and roles.

**Response 200:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "roles": ["applicant"],
  "created_at": "2026-02-13T10:00:00Z"
}
```

### 2.3 Update User Profile

```
PUT /api/v1/auth/me
```

**Auth Required:** Yes (any role)

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-0123"
}
```

**Response 200:** Updated user object.

---

## 3. Loan Products

### 3.1 List Loan Products

```
GET /api/v1/loans
```

**Auth Required:** Yes (any role)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by loan type (conventional, fha, va, usda, jumbo) |
| `term` | integer | Filter by term in years |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "30-Year Fixed-Rate Conventional",
      "type": "conventional",
      "term_years": 30,
      "rate_type": "fixed",
      "min_down_payment_pct": 3.0,
      "min_credit_score": 620,
      "max_dti_ratio": 43.0,
      "max_loan_amount": 766550,
      "description": "Standard fixed-rate mortgage with predictable monthly payments.",
      "eligibility_requirements": [
        "Minimum credit score of 620",
        "Debt-to-income ratio below 43%",
        "Minimum 3% down payment"
      ],
      "features": [
        "Fixed interest rate for the life of the loan",
        "PMI required if down payment < 20%",
        "No prepayment penalties"
      ]
    }
  ],
  "total": 8
}
```

### 3.2 Get Loan Product Details

```
GET /api/v1/loans/{loan_id}
```

**Auth Required:** Yes (any role)

**Response 200:** Single loan product object (same schema as list item).

### 3.3 Loan Eligibility Pre-Check

```
POST /api/v1/loans/{loan_id}/eligibility-check
```

**Auth Required:** Yes (`applicant`)

**Description:** Quick pre-qualification check before full application.

**Request Body:**
```json
{
  "annual_income": 85000,
  "monthly_debts": 1200,
  "credit_score_range": "620-679",
  "down_payment_amount": 25000,
  "property_value": 350000,
  "citizenship_status": "permanent_resident"
}
```

**Response 200:**
```json
{
  "eligible": true,
  "estimated_rate": "6.5% - 7.0%",
  "estimated_monthly_payment": 2200,
  "max_loan_amount": 325000,
  "warnings": [
    "Credit score is near the minimum threshold. A higher score may qualify for better rates."
  ],
  "suggestions": [
    "Consider a larger down payment to avoid PMI."
  ]
}
```

---

## 4. Applications

### 4.1 Create Application

```
POST /api/v1/applications
```

**Auth Required:** Yes (`applicant`)

**Request Body:**
```json
{
  "loan_product_id": "uuid",
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "ssn_last_four": "1234",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": {
      "street": "123 Main St",
      "city": "Springfield",
      "state": "IL",
      "zip_code": "62704"
    },
    "citizenship_status": "citizen",
    "visa_type": null,
    "years_in_country": null
  },
  "employment_info": {
    "employment_status": "employed",
    "employer_name": "Acme Corp",
    "job_title": "Software Engineer",
    "years_at_current_job": 3,
    "years_in_field": 8,
    "annual_income": 95000,
    "additional_income": 5000,
    "additional_income_source": "freelance",
    "is_self_employed": false
  },
  "financial_info": {
    "credit_score_self_reported": 720,
    "has_credit_history": true,
    "monthly_debts": {
      "car_loan": 350,
      "student_loans": 400,
      "credit_cards": 150,
      "other": 0
    },
    "total_assets": 120000,
    "liquid_assets": 45000,
    "checking_balance": 8000,
    "savings_balance": 37000,
    "retirement_accounts": 75000,
    "investment_accounts": 0,
    "bankruptcy_history": false,
    "foreclosure_history": false
  },
  "property_info": {
    "property_type": "single_family",
    "property_use": "primary_residence",
    "purchase_price": 350000,
    "down_payment": 70000,
    "address": {
      "street": "456 Oak Ave",
      "city": "Springfield",
      "state": "IL",
      "zip_code": "62701"
    }
  },
  "declarations": {
    "outstanding_judgments": false,
    "party_to_lawsuit": false,
    "federal_debt_delinquent": false,
    "alimony_obligation": false,
    "co_signer_on_other_loan": false,
    "us_citizen": true,
    "primary_residence": true
  }
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "application_number": "MA-2026-00001",
  "status": "draft",
  "loan_product_id": "uuid",
  "applicant_id": "uuid",
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T10:00:00Z"
}
```

### 4.2 Get Application

```
GET /api/v1/applications/{application_id}
```

**Auth Required:** Yes (`applicant` for own, `loan_servicer`/`admin` for any)

**Response 200:**
```json
{
  "id": "uuid",
  "application_number": "MA-2026-00001",
  "status": "under_review",
  "loan_product": { "...loan product object..." },
  "personal_info": { "..." },
  "employment_info": { "..." },
  "financial_info": { "..." },
  "property_info": { "..." },
  "declarations": { "..." },
  "documents": [
    {
      "id": "uuid",
      "type": "pay_stub",
      "filename": "paystub_jan2026.pdf",
      "status": "processed",
      "uploaded_at": "2026-02-13T11:00:00Z"
    }
  ],
  "risk_assessment": {
    "status": "completed",
    "id": "uuid"
  },
  "decision": null,
  "applicant_id": "uuid",
  "assigned_servicer_id": null,
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T12:00:00Z",
  "submitted_at": "2026-02-13T11:30:00Z"
}
```

### 4.3 Update Application (Draft Only)

```
PUT /api/v1/applications/{application_id}
```

**Auth Required:** Yes (`applicant`, own application, status must be `draft`)

**Request Body:** Same as create (partial updates allowed).

**Response 200:** Updated application object.

### 4.4 Submit Application

```
POST /api/v1/applications/{application_id}/submit
```

**Auth Required:** Yes (`applicant`, own application, status must be `draft`)

**Description:** Finalizes the application, triggers document validation and AI risk assessment pipeline.

**Response 200:**
```json
{
  "id": "uuid",
  "status": "submitted",
  "submitted_at": "2026-02-13T11:30:00Z",
  "message": "Application submitted successfully. Risk assessment has been initiated."
}
```

### 4.5 List Applications

```
GET /api/v1/applications
```

**Auth Required:** Yes

**Behavior by role:**
- `applicant`: Returns only their own applications
- `loan_servicer`: Returns all applications (filterable)
- `admin`: Returns all applications

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `risk_rating` | string | Filter by risk band (low, medium, high, very_high) |
| `assigned_to_me` | boolean | Servicer: show only my assigned applications |
| `limit` | integer | Page size (default 20, max 100) |
| `offset` | integer | Page offset |
| `sort_by` | string | Sort field (created_at, submitted_at, risk_score) |
| `sort_order` | string | asc or desc |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "application_number": "MA-2026-00001",
      "status": "under_review",
      "applicant_name": "John Doe",
      "loan_type": "30-Year Fixed-Rate Conventional",
      "loan_amount": 280000,
      "risk_score": 72,
      "risk_band": "medium",
      "submitted_at": "2026-02-13T11:30:00Z",
      "assigned_servicer": "Jane Smith"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

### 4.6 Application Status Values

| Status | Description |
|--------|-------------|
| `draft` | Application started but not submitted |
| `submitted` | Submitted, awaiting document processing |
| `documents_processing` | Documents being processed by OCR agent |
| `risk_assessment_in_progress` | AI agents analyzing application |
| `under_review` | AI assessment complete, awaiting servicer review |
| `additional_info_requested` | Servicer requested more information |
| `approved` | Loan approved by servicer |
| `conditionally_approved` | Approved with conditions |
| `denied` | Loan denied |
| `withdrawn` | Applicant withdrew application |

---

## 5. Documents

### 5.1 Upload Document

```
POST /api/v1/applications/{application_id}/documents
```

**Auth Required:** Yes (`applicant`, own application)

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | yes | Document file (PDF, PNG, JPG, max 10MB) |
| `document_type` | string | yes | Type of document (see table below) |
| `description` | string | no | Optional description |

**Document Types:**
| Type | Description |
|------|-------------|
| `government_id` | Government-issued photo ID |
| `pay_stub` | Recent pay stubs (last 2-3 months) |
| `w2` | W-2 wage statement |
| `tax_return` | Federal tax return (1-2 years) |
| `bank_statement` | Bank statement (last 2-3 months) |
| `employment_letter` | Employment verification letter |
| `proof_of_assets` | Investment/retirement account statements |
| `purchase_agreement` | Property purchase agreement |
| `rental_history` | Proof of rental payment history |
| `other` | Other supporting documents |

**Response 201:**
```json
{
  "id": "uuid",
  "application_id": "uuid",
  "document_type": "pay_stub",
  "filename": "paystub_jan2026.pdf",
  "file_size": 245000,
  "mime_type": "application/pdf",
  "status": "uploaded",
  "uploaded_at": "2026-02-13T11:00:00Z"
}
```

### 5.2 List Documents

```
GET /api/v1/applications/{application_id}/documents
```

**Auth Required:** Yes (`applicant` for own, `loan_servicer`/`admin` for any)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "document_type": "pay_stub",
      "filename": "paystub_jan2026.pdf",
      "file_size": 245000,
      "status": "processed",
      "extracted_data": {
        "employer": "Acme Corp",
        "pay_period": "2026-01-01 to 2026-01-15",
        "gross_pay": 3653.85,
        "net_pay": 2750.00
      },
      "uploaded_at": "2026-02-13T11:00:00Z",
      "processed_at": "2026-02-13T11:02:00Z"
    }
  ],
  "total": 5
}
```

### 5.3 Download Document

```
GET /api/v1/applications/{application_id}/documents/{document_id}/download
```

**Auth Required:** Yes (`applicant` for own, `loan_servicer`/`admin` for any)

**Response 200:** Returns a pre-signed URL for secure download.

```json
{
  "download_url": "https://minio.internal/mortgage-docs/...",
  "expires_in_seconds": 900
}
```

### 5.4 Delete Document

```
DELETE /api/v1/applications/{application_id}/documents/{document_id}
```

**Auth Required:** Yes (`applicant`, own application, status must be `draft`)

**Response 204:** No content.

---

## 6. Risk Assessment

### 6.1 Get Risk Assessment

```
GET /api/v1/applications/{application_id}/risk-assessment
```

**Auth Required:** Yes (`applicant` for own summary, `loan_servicer`/`admin` for full)

**Response 200 (Full - Loan Servicer View):**
```json
{
  "id": "uuid",
  "application_id": "uuid",
  "status": "completed",
  "overall_score": 72,
  "risk_band": "medium",
  "confidence": 0.85,
  "recommendation": "approve_with_conditions",
  "summary": "The applicant presents a moderate risk profile. Strong employment stability and income offset a below-average credit score. The credit trajectory is positive, showing consistent improvement over the past 18 months.",
  "dimensions": [
    {
      "name": "Credit History & Trajectory",
      "score": 58,
      "weight": 0.20,
      "weighted_score": 11.6,
      "agent": "credit_analysis",
      "positive_factors": [
        "Credit score improved from 620 to 720 over 18 months",
        "12 months of consecutive on-time payments",
        "Low credit utilization (22%)"
      ],
      "risk_factors": [
        "Limited credit history (3 years)",
        "One late payment 14 months ago"
      ],
      "mitigating_factors": [
        "Late payment was during job transition, resolved immediately",
        "Active credit-building behavior (secured card, small installment loan)"
      ],
      "explanation": "While the credit score itself is average, the trajectory is strongly positive. The applicant has demonstrated deliberate credit-building behavior and financial discipline."
    },
    {
      "name": "Employment & Income",
      "score": 85,
      "weight": 0.20,
      "weighted_score": 17.0,
      "agent": "employment_verification",
      "positive_factors": [
        "3 years at current employer (Acme Corp)",
        "8 years in field (Software Engineering)",
        "Stable income with year-over-year growth",
        "Employer is Fortune 500 company"
      ],
      "risk_factors": [],
      "mitigating_factors": [],
      "explanation": "Strong employment profile with above-average stability and income growth trajectory."
    },
    {
      "name": "Financial Health",
      "score": 70,
      "weight": 0.15,
      "weighted_score": 10.5,
      "agent": "financial_health",
      "positive_factors": [
        "6 months of mortgage payments in liquid reserves",
        "Consistent savings pattern (positive trend)",
        "Retirement contributions show long-term planning"
      ],
      "risk_factors": [
        "DTI ratio at 36% (manageable but not low)"
      ],
      "mitigating_factors": [
        "Student loan payments will end in 2 years, reducing DTI to 28%"
      ],
      "explanation": "Adequate financial reserves with room for improvement in DTI ratio."
    },
    {
      "name": "Property & Collateral",
      "score": 78,
      "weight": 0.15,
      "weighted_score": 11.7,
      "agent": "property_valuation",
      "positive_factors": [
        "LTV ratio of 80% (standard)",
        "Property in appreciating market",
        "Good condition, no major repairs needed"
      ],
      "risk_factors": [],
      "mitigating_factors": [],
      "explanation": "Property represents solid collateral with favorable market conditions."
    },
    {
      "name": "Applicant Profile",
      "score": 75,
      "weight": 0.10,
      "weighted_score": 7.5,
      "agent": "applicant_profile",
      "positive_factors": [
        "US citizen",
        "Bachelor's degree in Computer Science",
        "High-growth industry"
      ],
      "risk_factors": [],
      "mitigating_factors": [],
      "explanation": "Strong personal profile with favorable career trajectory."
    },
    {
      "name": "Behavioral Patterns",
      "score": 72,
      "weight": 0.10,
      "weighted_score": 7.2,
      "agent": "financial_health",
      "positive_factors": [
        "24 months of on-time rent payments",
        "All utility bills paid on time",
        "No overdrafts in 18 months"
      ],
      "risk_factors": [
        "2 overdrafts 20 months ago"
      ],
      "mitigating_factors": [
        "Overdrafts occurred during job transition, pattern resolved"
      ],
      "explanation": "Consistent responsible financial behavior with minor historical issues during life transition."
    },
    {
      "name": "Regulatory Compliance",
      "score": 100,
      "weight": 0.10,
      "weighted_score": 10.0,
      "agent": "regulatory_compliance",
      "positive_factors": [
        "No fair lending concerns identified",
        "All required disclosures can be made",
        "Application meets all regulatory requirements"
      ],
      "risk_factors": [],
      "mitigating_factors": [],
      "explanation": "Application is fully compliant with all applicable regulations."
    }
  ],
  "conditions": [
    "Verify employment with current employer within 10 business days",
    "Provide most recent bank statement (within 30 days)"
  ],
  "processing_metadata": {
    "started_at": "2026-02-13T11:31:00Z",
    "completed_at": "2026-02-13T11:33:45Z",
    "duration_seconds": 165,
    "llm_provider": "openai",
    "model": "gpt-4o",
    "total_tokens_used": 12450
  }
}
```

**Response 200 (Summary - Applicant View):**
```json
{
  "id": "uuid",
  "status": "completed",
  "overall_score": 72,
  "risk_band": "medium",
  "recommendation": "approve_with_conditions",
  "summary": "Your application has been assessed and is under review by a loan officer. Based on our analysis, your application shows strong employment stability and improving credit history.",
  "positive_highlights": [
    "Strong employment stability",
    "Improving credit trajectory",
    "Adequate savings reserves"
  ],
  "areas_of_concern": [
    "Credit history is shorter than average",
    "Debt-to-income ratio is manageable but could be lower"
  ]
}
```

### 6.2 Retry Risk Assessment

```
POST /api/v1/applications/{application_id}/risk-assessment/retry
```

**Auth Required:** Yes (`loan_servicer`, `admin`)

**Description:** Re-runs the AI risk assessment (e.g., after additional documents uploaded).

**Response 202:**
```json
{
  "message": "Risk assessment re-initiated.",
  "status": "risk_assessment_in_progress"
}
```

---

## 7. Decisions

### 7.1 Get Decision

```
GET /api/v1/applications/{application_id}/decision
```

**Auth Required:** Yes (`applicant` for own, `loan_servicer`/`admin` for any)

**Response 200:**
```json
{
  "id": "uuid",
  "application_id": "uuid",
  "decision": "approved",
  "ai_recommendation": "approve_with_conditions",
  "servicer_agreed_with_ai": true,
  "conditions": [
    "Employment verification required within 10 business days"
  ],
  "interest_rate": 6.75,
  "loan_amount": 280000,
  "term_years": 30,
  "monthly_payment": 1816.36,
  "explanation": "Your mortgage application has been approved. You have demonstrated strong employment stability, responsible financial behavior, and an improving credit profile.",
  "adverse_action_reasons": null,
  "decided_by": {
    "id": "uuid",
    "name": "Jane Smith",
    "role": "loan_servicer"
  },
  "decided_at": "2026-02-13T14:00:00Z"
}
```

### 7.2 Create Decision (Approve)

```
POST /api/v1/applications/{application_id}/decision
```

**Auth Required:** Yes (`loan_servicer`)

**Request Body:**
```json
{
  "decision": "approved",
  "conditions": [
    "Employment verification required within 10 business days"
  ],
  "interest_rate": 6.75,
  "notes": "Strong application. AI assessment aligns with my review.",
  "override_ai_recommendation": false,
  "override_justification": null
}
```

### 7.3 Create Decision (Deny)

```
POST /api/v1/applications/{application_id}/decision
```

**Auth Required:** Yes (`loan_servicer`)

**Request Body:**
```json
{
  "decision": "denied",
  "adverse_action_reasons": [
    "Debt-to-income ratio exceeds program limits",
    "Insufficient credit history"
  ],
  "notes": "DTI at 52% exceeds the 43% maximum for this loan program.",
  "override_ai_recommendation": true,
  "override_justification": "AI recommended conditional approval, but DTI is too high even with mitigating factors."
}
```

### 7.4 Request Additional Information

```
POST /api/v1/applications/{application_id}/request-info
```

**Auth Required:** Yes (`loan_servicer`)

**Request Body:**
```json
{
  "requested_items": [
    {
      "type": "document",
      "document_type": "bank_statement",
      "description": "Most recent bank statement (within 30 days)"
    },
    {
      "type": "clarification",
      "question": "Please explain the $5,000 deposit on January 15th in your checking account."
    }
  ],
  "due_date": "2026-02-20"
}
```

**Response 200:**
```json
{
  "application_id": "uuid",
  "status": "additional_info_requested",
  "requested_items": [...],
  "due_date": "2026-02-20",
  "message": "Applicant has been notified of the information request."
}
```

---

## 8. Servicer Endpoints

### 8.1 Assign Application

```
POST /api/v1/applications/{application_id}/assign
```

**Auth Required:** Yes (`loan_servicer`, `admin`)

**Request Body:**
```json
{
  "servicer_id": "uuid"
}
```

### 8.2 Servicer Dashboard Stats

```
GET /api/v1/servicer/dashboard
```

**Auth Required:** Yes (`loan_servicer`)

**Response 200:**
```json
{
  "pending_review": 12,
  "in_progress": 5,
  "decided_today": 8,
  "average_processing_time_hours": 4.2,
  "approval_rate": 0.73,
  "risk_distribution": {
    "low": 15,
    "medium": 22,
    "high": 8,
    "very_high": 3
  },
  "recent_applications": [...]
}
```

---

## 9. Admin Endpoints

### 9.1 LLM Provider Configuration

```
GET /api/v1/admin/llm-config
PUT /api/v1/admin/llm-config
```

**Auth Required:** Yes (`admin`)

**PUT Request Body:**
```json
{
  "active_provider": "openai",
  "providers": {
    "openai": {
      "enabled": true,
      "base_url": "https://api.openai.com/v1",
      "api_key": "sk-...",
      "default_model": "gpt-4o",
      "max_tokens": 4096,
      "temperature": 0.1,
      "rate_limit_rpm": 60
    },
    "anthropic": {
      "enabled": true,
      "base_url": "https://api.anthropic.com",
      "api_key": "sk-ant-...",
      "default_model": "claude-sonnet-4-20250514",
      "max_tokens": 4096,
      "temperature": 0.1,
      "rate_limit_rpm": 60
    },
    "local": {
      "enabled": false,
      "base_url": "https://llm.internal.company.com/v1",
      "api_key": "",
      "default_model": "llama-3.1-70b",
      "max_tokens": 4096,
      "temperature": 0.1,
      "rate_limit_rpm": 0
    }
  }
}
```

### 9.2 System Health

```
GET /api/v1/admin/health/detailed
```

**Auth Required:** Yes (`admin`)

**Response 200:**
```json
{
  "api": { "status": "healthy", "uptime_seconds": 86400 },
  "database": { "status": "healthy", "connections_active": 5, "connections_max": 20 },
  "redis": { "status": "healthy", "memory_used_mb": 45 },
  "minio": { "status": "healthy", "storage_used_gb": 2.3 },
  "celery": { "status": "healthy", "active_workers": 2, "queued_tasks": 3 },
  "keycloak": { "status": "healthy" },
  "llm_providers": {
    "openai": { "status": "healthy", "latency_ms": 230 },
    "anthropic": { "status": "healthy", "latency_ms": 180 },
    "local": { "status": "unavailable" }
  }
}
```

### 9.3 Audit Log

```
GET /api/v1/admin/audit-log
```

**Auth Required:** Yes (`admin`)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action type |
| `user_id` | string | Filter by user |
| `resource_type` | string | Filter by resource (application, document, decision) |
| `from_date` | datetime | Start date |
| `to_date` | datetime | End date |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "timestamp": "2026-02-13T14:00:00Z",
      "action": "decision_created",
      "user_id": "uuid",
      "user_name": "Jane Smith",
      "user_role": "loan_servicer",
      "resource_type": "decision",
      "resource_id": "uuid",
      "details": {
        "application_id": "uuid",
        "decision": "approved",
        "override_ai": false
      }
    }
  ],
  "total": 1250
}
```

---

## 10. Health Check

### 10.1 Basic Health

```
GET /api/v1/health
```

**Auth Required:** No

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-13T10:00:00Z"
}
```

---

## 11. WebSocket: Real-Time Updates

### 11.1 Application Status Updates

```
WS /api/v1/ws/applications/{application_id}
```

**Auth Required:** Yes (JWT token as query parameter)

**Description:** Real-time updates on application processing progress.

**Message Types (Server → Client):**

```json
{
  "type": "status_change",
  "data": {
    "status": "risk_assessment_in_progress",
    "message": "AI agents are analyzing your application..."
  }
}
```

```json
{
  "type": "agent_progress",
  "data": {
    "agent": "credit_analysis",
    "status": "completed",
    "progress_pct": 40,
    "message": "Credit history analysis complete."
  }
}
```

```json
{
  "type": "assessment_complete",
  "data": {
    "risk_score": 72,
    "risk_band": "medium",
    "recommendation": "approve_with_conditions"
  }
}
```

```json
{
  "type": "decision_made",
  "data": {
    "decision": "approved",
    "message": "Your application has been approved!"
  }
}
```

### 11.2 Servicer Notifications

```
WS /api/v1/ws/servicer/notifications
```

**Auth Required:** Yes (`loan_servicer`)

**Message Types:**

```json
{
  "type": "new_application",
  "data": {
    "application_id": "uuid",
    "applicant_name": "John Doe",
    "loan_type": "30-Year Fixed",
    "risk_band": "medium"
  }
}
```

```json
{
  "type": "info_response_received",
  "data": {
    "application_id": "uuid",
    "applicant_name": "John Doe",
    "items_received": 2
  }
}
```
