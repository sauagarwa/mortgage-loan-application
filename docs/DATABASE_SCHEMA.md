# MortgageAI: Database Schema

**Version:** 1.0
**Date:** 2026-02-13
**Database:** PostgreSQL 16 with pgvector extension

---

## 1. Entity-Relationship Overview

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐
│   user   │────<│  application  │────<│   document   │
└──────────┘     └───────┬───────┘     └──────────────┘
                         │
                         │
              ┌──────────┴──────────┐
              │                     │
     ┌────────▼────────┐   ┌───────▼────────┐
     │ risk_assessment │   │    decision     │
     └────────┬────────┘   └────────────────┘
              │
     ┌────────▼────────────┐
     │ risk_dimension_score │
     └─────────────────────┘

┌──────────────┐     ┌───────────────┐
│ loan_product │     │  audit_log    │
└──────────────┘     └───────────────┘

┌───────────────┐    ┌────────────────────┐
│  llm_config   │    │ info_request       │
└───────────────┘    └────────────────────┘
```

---

## 2. Table Definitions

### 2.1 `user`

Synced from Keycloak. Stores local user profile data and role mapping.

```sql
CREATE TABLE "user" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_id     VARCHAR(255) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(20),
    role            VARCHAR(50) NOT NULL DEFAULT 'applicant',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_login_at   TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_keycloak_id ON "user" (keycloak_id);
CREATE INDEX idx_user_email ON "user" (email);
CREATE INDEX idx_user_role ON "user" (role);
```

**Columns:**
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| keycloak_id | VARCHAR(255) | No | Keycloak user ID (unique) |
| email | VARCHAR(255) | No | User email (unique) |
| first_name | VARCHAR(100) | No | First name |
| last_name | VARCHAR(100) | No | Last name |
| phone | VARCHAR(20) | Yes | Phone number |
| role | VARCHAR(50) | No | User role: applicant, loan_servicer, admin |
| is_active | BOOLEAN | No | Account active status |
| last_login_at | TIMESTAMPTZ | Yes | Last login timestamp |
| created_at | TIMESTAMPTZ | No | Record creation time |
| updated_at | TIMESTAMPTZ | No | Last update time |

---

### 2.2 `loan_product`

Catalog of available mortgage loan products.

```sql
CREATE TABLE loan_product (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(200) NOT NULL,
    type                    VARCHAR(50) NOT NULL,
    term_years              INTEGER NOT NULL,
    rate_type               VARCHAR(20) NOT NULL,
    min_down_payment_pct    DECIMAL(5,2) NOT NULL,
    min_credit_score        INTEGER,
    max_dti_ratio           DECIMAL(5,2),
    max_loan_amount         DECIMAL(15,2),
    description             TEXT,
    eligibility_requirements JSONB NOT NULL DEFAULT '[]',
    features                JSONB NOT NULL DEFAULT '[]',
    is_active               BOOLEAN NOT NULL DEFAULT true,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_loan_product_type ON loan_product (type);
CREATE INDEX idx_loan_product_active ON loan_product (is_active);
```

**Columns:**
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| name | VARCHAR(200) | No | Product display name |
| type | VARCHAR(50) | No | conventional, fha, va, usda, jumbo |
| term_years | INTEGER | No | Loan term in years |
| rate_type | VARCHAR(20) | No | fixed, adjustable |
| min_down_payment_pct | DECIMAL(5,2) | No | Minimum down payment percentage |
| min_credit_score | INTEGER | Yes | Minimum credit score (null = no minimum) |
| max_dti_ratio | DECIMAL(5,2) | Yes | Maximum DTI ratio |
| max_loan_amount | DECIMAL(15,2) | Yes | Maximum loan amount |
| description | TEXT | Yes | Product description |
| eligibility_requirements | JSONB | No | Array of requirement strings |
| features | JSONB | No | Array of feature strings |
| is_active | BOOLEAN | No | Whether product is currently offered |
| created_at | TIMESTAMPTZ | No | Record creation time |
| updated_at | TIMESTAMPTZ | No | Last update time |

---

### 2.3 `application`

Central table for mortgage loan applications.

```sql
CREATE TABLE application (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_number  VARCHAR(20) UNIQUE NOT NULL,
    applicant_id        UUID NOT NULL REFERENCES "user" (id),
    loan_product_id     UUID NOT NULL REFERENCES loan_product (id),
    assigned_servicer_id UUID REFERENCES "user" (id),
    status              VARCHAR(50) NOT NULL DEFAULT 'draft',

    -- Personal Information
    personal_info       JSONB NOT NULL DEFAULT '{}',

    -- Employment Information
    employment_info     JSONB NOT NULL DEFAULT '{}',

    -- Financial Information
    financial_info      JSONB NOT NULL DEFAULT '{}',

    -- Property Information
    property_info       JSONB NOT NULL DEFAULT '{}',

    -- Declarations
    declarations        JSONB NOT NULL DEFAULT '{}',

    -- Computed fields
    loan_amount         DECIMAL(15,2),
    down_payment        DECIMAL(15,2),
    dti_ratio           DECIMAL(5,2),

    -- Timestamps
    submitted_at        TIMESTAMP WITH TIME ZONE,
    decided_at          TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_application_applicant ON application (applicant_id);
CREATE INDEX idx_application_servicer ON application (assigned_servicer_id);
CREATE INDEX idx_application_status ON application (status);
CREATE INDEX idx_application_number ON application (application_number);
CREATE INDEX idx_application_submitted ON application (submitted_at);
CREATE INDEX idx_application_loan_product ON application (loan_product_id);
```

**Status Values:**
`draft`, `submitted`, `documents_processing`, `risk_assessment_in_progress`, `under_review`, `additional_info_requested`, `approved`, `conditionally_approved`, `denied`, `withdrawn`

**JSONB Field: `personal_info`**
```json
{
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "date",
  "ssn_last_four": "string (encrypted)",
  "email": "string",
  "phone": "string",
  "address": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip_code": "string"
  },
  "citizenship_status": "citizen|permanent_resident|visa_holder|other",
  "visa_type": "string|null",
  "years_in_country": "integer|null"
}
```

**JSONB Field: `employment_info`**
```json
{
  "employment_status": "employed|self_employed|unemployed|retired",
  "employer_name": "string",
  "job_title": "string",
  "years_at_current_job": "number",
  "years_in_field": "number",
  "annual_income": "number",
  "additional_income": "number",
  "additional_income_source": "string",
  "is_self_employed": "boolean"
}
```

**JSONB Field: `financial_info`**
```json
{
  "credit_score_self_reported": "integer",
  "has_credit_history": "boolean",
  "monthly_debts": {
    "car_loan": "number",
    "student_loans": "number",
    "credit_cards": "number",
    "other": "number"
  },
  "total_assets": "number",
  "liquid_assets": "number",
  "checking_balance": "number",
  "savings_balance": "number",
  "retirement_accounts": "number",
  "investment_accounts": "number",
  "bankruptcy_history": "boolean",
  "foreclosure_history": "boolean"
}
```

**JSONB Field: `property_info`**
```json
{
  "property_type": "single_family|condo|townhouse|multi_family",
  "property_use": "primary_residence|secondary|investment",
  "purchase_price": "number",
  "down_payment": "number",
  "address": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip_code": "string"
  }
}
```

---

### 2.4 `document`

Uploaded documents and their OCR-extracted data.

```sql
CREATE TABLE document (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES application (id) ON DELETE CASCADE,
    document_type   VARCHAR(50) NOT NULL,
    filename        VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    file_size       INTEGER NOT NULL,
    storage_key     VARCHAR(500) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'uploaded',
    extracted_data  JSONB,
    extraction_confidence DECIMAL(3,2),
    processing_error TEXT,
    uploaded_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    processed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_document_application ON document (application_id);
CREATE INDEX idx_document_type ON document (document_type);
CREATE INDEX idx_document_status ON document (status);
```

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| application_id | UUID | FK to application |
| document_type | VARCHAR(50) | government_id, pay_stub, w2, tax_return, bank_statement, etc. |
| filename | VARCHAR(500) | Stored filename (UUID-based) |
| original_filename | VARCHAR(500) | Original upload filename |
| mime_type | VARCHAR(100) | application/pdf, image/png, etc. |
| file_size | INTEGER | File size in bytes |
| storage_key | VARCHAR(500) | MinIO object key |
| status | VARCHAR(30) | uploaded, processing, processed, failed |
| extracted_data | JSONB | OCR-extracted structured data |
| extraction_confidence | DECIMAL(3,2) | OCR confidence score (0.00 - 1.00) |
| processing_error | TEXT | Error message if processing failed |

---

### 2.5 `risk_assessment`

Top-level risk assessment results for an application.

```sql
CREATE TABLE risk_assessment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES application (id),
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    overall_score   DECIMAL(5,2),
    risk_band       VARCHAR(20),
    confidence      DECIMAL(3,2),
    recommendation  VARCHAR(50),
    summary         TEXT,
    conditions      JSONB DEFAULT '[]',
    llm_provider    VARCHAR(50),
    llm_model       VARCHAR(100),
    total_tokens    INTEGER,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    error_message   TEXT,
    attempt_number  INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_risk_assessment_application ON risk_assessment (application_id);
CREATE INDEX idx_risk_assessment_status ON risk_assessment (status);
```

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| overall_score | DECIMAL(5,2) | Composite risk score (0-100) |
| risk_band | VARCHAR(20) | low (75-100), medium (50-74), high (25-49), very_high (0-24) |
| confidence | DECIMAL(3,2) | AI confidence in assessment (0.00 - 1.00) |
| recommendation | VARCHAR(50) | approve, approve_with_conditions, deny, manual_review |
| summary | TEXT | Natural language assessment summary |
| conditions | JSONB | Array of conditions for conditional approval |
| llm_provider | VARCHAR(50) | Which LLM provider was used |
| llm_model | VARCHAR(100) | Which model was used |
| total_tokens | INTEGER | Total tokens consumed |
| attempt_number | INTEGER | Retry attempt number |

---

### 2.6 `risk_dimension_score`

Individual dimension scores from each MCP agent.

```sql
CREATE TABLE risk_dimension_score (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_assessment_id  UUID NOT NULL REFERENCES risk_assessment (id) ON DELETE CASCADE,
    dimension_name      VARCHAR(100) NOT NULL,
    agent_name          VARCHAR(100) NOT NULL,
    score               DECIMAL(5,2) NOT NULL,
    weight              DECIMAL(3,2) NOT NULL,
    weighted_score      DECIMAL(5,2) NOT NULL,
    positive_factors    JSONB NOT NULL DEFAULT '[]',
    risk_factors        JSONB NOT NULL DEFAULT '[]',
    mitigating_factors  JSONB NOT NULL DEFAULT '[]',
    explanation         TEXT,
    raw_agent_output    JSONB,
    tokens_used         INTEGER,
    processing_time_ms  INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_risk_dimension_assessment ON risk_dimension_score (risk_assessment_id);
CREATE INDEX idx_risk_dimension_agent ON risk_dimension_score (agent_name);
```

---

### 2.7 `decision`

Final loan decision made by the servicer.

```sql
CREATE TABLE decision (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id          UUID NOT NULL REFERENCES application (id) UNIQUE,
    risk_assessment_id      UUID REFERENCES risk_assessment (id),
    decided_by              UUID NOT NULL REFERENCES "user" (id),
    decision                VARCHAR(30) NOT NULL,
    ai_recommendation       VARCHAR(50),
    servicer_agreed_with_ai BOOLEAN,
    override_justification  TEXT,
    conditions              JSONB DEFAULT '[]',
    adverse_action_reasons  JSONB DEFAULT '[]',
    interest_rate           DECIMAL(5,3),
    approved_loan_amount    DECIMAL(15,2),
    approved_term_years     INTEGER,
    monthly_payment         DECIMAL(10,2),
    notes                   TEXT,
    decided_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_decision_application ON decision (application_id);
CREATE INDEX idx_decision_decided_by ON decision (decided_by);
CREATE INDEX idx_decision_type ON decision (decision);
CREATE INDEX idx_decision_date ON decision (decided_at);
```

**Decision Values:**
`approved`, `conditionally_approved`, `denied`

---

### 2.8 `info_request`

Tracks additional information requests from servicers.

```sql
CREATE TABLE info_request (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES application (id),
    requested_by    UUID NOT NULL REFERENCES "user" (id),
    requested_items JSONB NOT NULL,
    due_date        DATE,
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    response_notes  TEXT,
    responded_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_info_request_application ON info_request (application_id);
CREATE INDEX idx_info_request_status ON info_request (status);
```

---

### 2.9 `llm_config`

LLM provider configuration (admin-managed).

```sql
CREATE TABLE llm_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider        VARCHAR(50) NOT NULL UNIQUE,
    is_active       BOOLEAN NOT NULL DEFAULT false,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    base_url        VARCHAR(500) NOT NULL,
    api_key_encrypted VARCHAR(500),
    default_model   VARCHAR(100) NOT NULL,
    max_tokens      INTEGER NOT NULL DEFAULT 4096,
    temperature     DECIMAL(3,2) NOT NULL DEFAULT 0.10,
    rate_limit_rpm  INTEGER DEFAULT 60,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_llm_config_default ON llm_config (is_default) WHERE is_default = true;
```

---

### 2.10 `audit_log`

Immutable audit trail for all significant actions.

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    user_id         UUID REFERENCES "user" (id),
    user_email      VARCHAR(255),
    user_role       VARCHAR(50),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID,
    details         JSONB,
    ip_address      INET,
    user_agent      TEXT
);

-- Partitioned by month for performance
CREATE INDEX idx_audit_log_timestamp ON audit_log (timestamp);
CREATE INDEX idx_audit_log_user ON audit_log (user_id);
CREATE INDEX idx_audit_log_action ON audit_log (action);
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);
```

**Action Values:**
- `application_created`, `application_updated`, `application_submitted`, `application_withdrawn`
- `document_uploaded`, `document_processed`, `document_deleted`
- `risk_assessment_started`, `risk_assessment_completed`, `risk_assessment_failed`
- `decision_created`, `decision_overridden`
- `info_requested`, `info_provided`
- `user_login`, `user_logout`, `user_created`
- `llm_config_updated`, `system_config_updated`

---

### 2.11 `notification`

User notifications (in-app and email tracking).

```sql
CREATE TABLE notification (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES "user" (id),
    type            VARCHAR(50) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    application_id  UUID REFERENCES application (id),
    is_read         BOOLEAN NOT NULL DEFAULT false,
    email_sent      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_notification_user ON notification (user_id);
CREATE INDEX idx_notification_unread ON notification (user_id, is_read) WHERE is_read = false;
```

---

## 3. Migration Strategy

### 3.1 Migration Order

Migrations should be created in this order to respect foreign key dependencies:

1. `user` table
2. `loan_product` table
3. `application` table (depends on user, loan_product)
4. `document` table (depends on application)
5. `risk_assessment` table (depends on application)
6. `risk_dimension_score` table (depends on risk_assessment)
7. `decision` table (depends on application, risk_assessment, user)
8. `info_request` table (depends on application, user)
9. `llm_config` table (standalone)
10. `audit_log` table (loose FK to user)
11. `notification` table (depends on user, application)

### 3.2 Seed Data

**Loan Products** (seeded on first migration):
- 30-Year Fixed Conventional
- 15-Year Fixed Conventional
- 5/1 ARM Conventional
- 7/1 ARM Conventional
- FHA 30-Year Fixed
- VA 30-Year Fixed
- USDA 30-Year Fixed
- Jumbo 30-Year Fixed

**LLM Configurations** (seeded with defaults):
- OpenAI (default, active)
- Anthropic (inactive)
- Local (inactive)

### 3.3 Indexes Strategy

- **Primary queries** (frequently queried): Covered by indexes listed above
- **Composite indexes** to add based on query patterns:
  - `(applicant_id, status)` on application
  - `(assigned_servicer_id, status)` on application
  - `(application_id, document_type)` on document
- **Partial indexes** for performance:
  - Active applications only: `WHERE status NOT IN ('approved', 'denied', 'withdrawn')`
  - Unread notifications: `WHERE is_read = false`

---

## 4. Data Retention & Privacy

### 4.1 PII Fields

The following fields contain PII and require special handling:

| Table | Field | Treatment |
|-------|-------|-----------|
| user | email, first_name, last_name, phone | Encrypted at rest, masked in logs |
| application | personal_info.ssn_last_four | Application-level encryption |
| application | personal_info.date_of_birth | Encrypted at rest |
| document | File content | Encrypted in MinIO, auto-delete after decision + retention period |

### 4.2 Retention Policy

| Data Type | Retention | Action After |
|-----------|-----------|-------------|
| Active applications | Indefinite | N/A |
| Decided applications | 7 years | Archive to cold storage |
| Uploaded documents | 7 years after decision | Delete from MinIO |
| Audit logs | 10 years | Archive to cold storage |
| User accounts | Until deletion request | Anonymize, retain audit refs |

### 4.3 Right to Deletion

When a user requests deletion:
1. Anonymize `user` record (replace PII with `[DELETED]`)
2. Anonymize `application.personal_info` fields
3. Delete documents from MinIO
4. Retain anonymized audit log entries (legal requirement)
5. Retain anonymized application data for fair lending reporting
