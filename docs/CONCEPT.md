# MortgageAI: Intelligent Mortgage Loan Origination & Approval Platform

## Concept Document

**Version:** 1.0
**Date:** 2026-02-13
**Status:** Draft

---

## 1. Executive Summary

MortgageAI is an AI-powered mortgage loan origination and approval platform that moves beyond traditional credit-score-only assessments to deliver holistic, fair, and explainable lending decisions. The platform uses multiple AI agents (via the Model Context Protocol) to analyze applicant profiles across dozens of financial, behavioral, and contextual dimensions, producing risk ratings with full explanations that loan servicers can review, override, and finalize.

The system supports multiple LLM backends (OpenAI, Anthropic, or self-hosted OpenAI-compatible models), Keycloak-based authentication, document upload and OCR processing, and a human-in-the-loop approval workflow.

---

## 2. Problem Statement

Traditional mortgage underwriting relies heavily on credit scores, which:

- **Exclude creditworthy individuals** who lack credit history (immigrants, young adults, self-employed workers)
- **Penalize temporary setbacks** without considering trajectory (e.g., someone recovering from medical debt)
- **Ignore contextual factors** such as stable employment, savings patterns, education, and community ties
- **Lack transparency** in decision-making, leading to applicant frustration and regulatory risk
- **Are slow and manual**, requiring extensive back-and-forth between applicants and underwriters

MortgageAI addresses these issues by creating a multi-dimensional risk assessment that considers the whole applicant, not just a single number.

---

## 3. Vision

**"Every creditworthy borrower deserves a fair, explainable, and efficient path to homeownership."**

MortgageAI will:
1. Assess applicants holistically using AI agents that analyze financial history, employment stability, behavioral patterns, and contextual factors
2. Provide transparent, explainable risk ratings with natural-language justifications
3. Empower loan servicers with AI-assisted decision support while keeping humans in the loop for final approval
4. Support diverse applicant profiles including non-citizens, first-time buyers, self-employed individuals, and those rebuilding credit

---

## 4. Key Stakeholders

### 4.1 Applicant (Borrower)
- Signs up and creates an account
- Selects loan type and fills out application
- Uploads required documents (ID, pay stubs, tax returns, bank statements)
- Tracks application status in real-time
- Receives AI-generated decision with explanation

### 4.2 Loan Servicer (Underwriter/Loan Officer)
- Reviews incoming applications with AI-generated risk assessments
- Views detailed risk breakdown across all assessment dimensions
- Can request additional information from applicants
- Makes final approval/denial decision (human-in-the-loop)
- Can override AI recommendation with documented justification

### 4.3 System Administrator
- Manages LLM provider configuration
- Configures risk assessment parameters and thresholds
- Manages user roles and permissions
- Monitors system health and audit logs

---

## 5. Core Capabilities

### 5.1 Multi-Dimensional Risk Assessment

Instead of relying solely on credit scores, MortgageAI evaluates applicants across these dimensions:

| Dimension | What It Measures | Why It Matters |
|-----------|-----------------|----------------|
| **Credit History & Trajectory** | Credit score, payment history, credit utilization, and trend direction | Shows not just where someone is, but where they're heading |
| **Employment & Income Stability** | Job tenure, employer type, income consistency, career trajectory | Predicts ability to maintain mortgage payments |
| **Debt-to-Income Ratio** | Total monthly debt obligations vs. gross monthly income | Standard affordability metric |
| **Asset & Savings Analysis** | Liquid assets, savings patterns, investment accounts, retirement funds | Indicates financial resilience and down payment capability |
| **Behavioral Financial Patterns** | Rent payment history, utility payments, subscription management | Shows financial responsibility beyond credit bureau data |
| **Property & Collateral Assessment** | Property value, location trends, comparable sales, condition | Evaluates the security of the loan |
| **Residency & Legal Status** | Citizenship, visa type, residency duration, legal work authorization | Affects loan eligibility and risk profile |
| **Education & Career Potential** | Education level, field of study, industry growth trends | Indicates future earning potential |
| **Banking Relationship** | Account longevity, banking patterns, overdraft history | Shows stability of financial relationships |
| **External Risk Factors** | Economic conditions, industry trends, regional housing market | Contextualizes individual risk within broader conditions |

### 5.2 AI-Powered Analysis via MCP Agents

Each risk dimension is analyzed by a specialized MCP (Model Context Protocol) agent:

- **Credit Analysis Agent** - Analyzes credit reports, identifies trends, and assesses trajectory
- **Employment Verification Agent** - Verifies employment data and assesses income stability
- **Document Processing Agent** - Extracts and validates data from uploaded documents via OCR
- **Financial Health Agent** - Analyzes bank statements, savings patterns, and asset composition
- **Property Valuation Agent** - Assesses property value and market conditions
- **Regulatory Compliance Agent** - Ensures fair lending compliance (ECOA, Fair Housing Act)
- **Risk Aggregation Agent** - Synthesizes all agent outputs into a holistic risk score with explanation
- **Applicant Profile Agent** - Considers residency status, education, career trajectory

### 5.3 Explainable Decisions

Every AI decision includes:
- **Risk Rating**: A composite score (1-100) with color-coded risk bands
- **Confidence Level**: How certain the AI is in its assessment
- **Positive Factors**: What strengthens the application
- **Risk Factors**: What concerns exist and their severity
- **Mitigating Factors**: Context that offsets risk factors
- **Natural Language Summary**: A plain-English explanation suitable for the applicant
- **Detailed Analysis**: Technical breakdown for the loan servicer

### 5.4 Loan Product Selection

The platform supports multiple loan types:
- **Conventional Fixed-Rate** (15, 20, 30 year)
- **Adjustable-Rate Mortgage (ARM)** (5/1, 7/1, 10/1)
- **FHA Loans** (lower down payment, flexible credit requirements)
- **VA Loans** (for veterans and service members)
- **USDA Loans** (rural property financing)
- **Jumbo Loans** (above conforming loan limits)

### 5.5 Document Management

Applicants can upload:
- Government-issued photo ID
- Proof of income (pay stubs, W-2s, tax returns)
- Bank statements (2-3 months)
- Employment verification letter
- Proof of assets (investment accounts, retirement funds)
- Property information (purchase agreement, appraisal)
- Additional supporting documents (rental payment history, utility bills)

Documents are processed by the Document Processing Agent which:
- Extracts text via OCR
- Validates document authenticity markers
- Extracts structured data (income amounts, employer names, account balances)
- Flags inconsistencies across documents

### 5.6 Authentication & Authorization

**Keycloak Integration:**
- OIDC/OAuth 2.0 authentication
- Role-based access control (RBAC)
- Self-service registration for applicants
- Federated identity (Google, Microsoft)

**Roles:**
| Role | Permissions |
|------|------------|
| `applicant` | Create/view own applications, upload documents, view decisions |
| `loan_servicer` | View all applications, review risk assessments, approve/deny |
| `admin` | System configuration, user management, audit logs |

### 5.7 LLM Provider Flexibility

The platform supports multiple LLM backends:

```
┌─────────────────────────────────────────┐
│           LLM Gateway Service           │
├─────────────┬──────────┬────────────────┤
│   OpenAI    │ Anthropic│  Local LLM     │
│  API Key    │ API Key  │  Base URL      │
│  Required   │ Required │  Optional Key  │
└─────────────┴──────────┴────────────────┘
```

Configuration per provider:
- **Provider type**: `openai`, `anthropic`, `local`
- **Base URL**: Default or custom (for local deployments)
- **API Key**: Required for cloud, optional for local
- **Model name**: Configurable per agent
- **Rate limiting**: Per-provider token/request limits

---

## 6. Application Workflow

### 6.1 Applicant Journey

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Sign Up │───>│  Select  │───>│   Fill   │───>│  Upload  │───>│  Submit  │
│  / Login │    │   Loan   │    │  Details │    │   Docs   │    │   App    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                                     │
     ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
     │ Decision │<───│   AI     │<───│   Risk   │<──────────────────┘
     │ Received │    │ Analysis │    │ Assessment│
     └──────────┘    └──────────┘    └──────────┘
```

1. **Registration**: Applicant signs up via Keycloak (email/password or social login)
2. **Loan Selection**: Browse available loan products with eligibility estimator
3. **Application Form**: Multi-step form collecting personal, financial, and property info
4. **Document Upload**: Upload required documents with real-time validation
5. **Submission**: Review and submit completed application
6. **AI Processing**: MCP agents analyze all data dimensions (async, with progress tracking)
7. **Decision Notification**: Applicant receives AI recommendation with explanation

### 6.2 Loan Servicer Journey

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Login   │───>│Dashboard │───>│  Review  │───>│  Verify  │───>│  Final   │
│          │    │  Queue   │    │   App    │    │  Details │    │ Decision │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. **Dashboard**: View all pending applications sorted by priority/risk
2. **Application Review**: Detailed view with AI risk assessment and explanation
3. **Risk Breakdown**: View each dimension's score, contributing factors, and agent reasoning
4. **Document Verification**: Review uploaded documents alongside extracted data
5. **Decision**: Accept AI recommendation, override with justification, or request more info
6. **Communication**: System notifies applicant of final decision

### 6.3 AI Processing Pipeline

```
Application Submitted
        │
        ▼
┌───────────────────┐
│ Document Processing│──── OCR, extraction, validation
│     Agent         │
└───────┬───────────┘
        │
        ▼ (parallel execution)
┌───────┴───────────────────────────────────────────────┐
│                                                        │
▼                ▼              ▼              ▼         ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐
│Credit  │ │Employ- │ │Financial │ │Property│ │Applicant│
│Analysis│ │ment    │ │Health    │ │Valua-  │ │Profile  │
│Agent   │ │Verif.  │ │Agent     │ │tion    │ │Agent    │
│        │ │Agent   │ │          │ │Agent   │ │         │
└───┬────┘ └───┬────┘ └────┬─────┘ └───┬────┘ └───┬────┘
    │          │           │           │           │
    └──────────┴───────────┴───────────┴───────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ Regulatory       │
                 │ Compliance Agent │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Risk Aggregation │──── Final score + explanation
                 │ Agent            │
                 └──────────────────┘
```

---

## 7. Non-Traditional Risk Factors: Detailed Analysis

### 7.1 Credit Trajectory (Not Just Credit Score)

Traditional: "Credit score is 580 → Deny"

MortgageAI approach:
- Score was 480 two years ago, now 580 → **Positive trajectory (+10 pts)**
- 18 months of on-time payments after prior defaults → **Recovery pattern (+8 pts)**
- Recently opened secured credit card, building history → **Active improvement (+5 pts)**
- Medical collections from 3 years ago, now resolved → **Circumstantial, not behavioral (+3 pts)**

### 7.2 Non-Citizen Applicants

Factors considered for non-citizen applicants:
- **Visa type and duration**: H-1B (3-6 years), L-1 (5-7 years), Green Card (permanent)
- **Employer sponsorship**: Indicates job stability and employer investment
- **Industry and role**: High-demand fields reduce visa-related employment risk
- **Time in country**: Longer residency shows stability
- **ITIN history**: Tax filing history demonstrates financial responsibility
- **Country of origin banking**: International credit references

### 7.3 First-Time Buyers Without Credit History

Alternative data considered:
- **Rent payment history** (12+ months of on-time payments)
- **Utility payment history** (electricity, gas, water, internet)
- **Mobile phone payment history**
- **Insurance premium payments**
- **Savings account patterns** (regular deposits, growing balance)
- **Education loan repayment** (if applicable)

### 7.4 Self-Employed / Gig Economy Workers

Special analysis:
- **Revenue trend** (2-3 years of tax returns)
- **Client diversity** (single vs. multiple income sources)
- **Industry stability** and demand projections
- **Business reserves** and emergency funds
- **Professional credentials** and certifications
- **Contract backlog** (future guaranteed income)

---

## 8. Technology Stack

### 8.1 Frontend (packages/ui)
- **React 19** + TypeScript
- **Vite** for build tooling
- **TanStack Router** for file-based routing
- **TanStack Query** for server state management
- **Tailwind CSS** + **shadcn/ui** for styling
- **Keycloak JS Adapter** for authentication
- **React Hook Form** + **Zod** for form validation

### 8.2 Backend (packages/api)
- **FastAPI** (Python 3.12+)
- **SQLAlchemy 2.0** async ORM
- **Pydantic v2** for validation
- **Alembic** for database migrations
- **python-keycloak** for auth integration
- **LiteLLM** or custom LLM gateway for multi-provider LLM support
- **Celery** + **Redis** for async task processing
- **MinIO/S3** for document storage

### 8.3 Database (packages/db)
- **PostgreSQL 16** with **pgvector** extension
- Structured data: Applications, users, decisions, audit logs
- Vector storage: Document embeddings for semantic search

### 8.4 AI/ML Layer
- **MCP (Model Context Protocol)** for agent orchestration
- **LangChain** or **LiteLLM** for LLM abstraction
- **Tesseract** or cloud OCR for document processing
- Support for: OpenAI, Anthropic, local OpenAI-compatible endpoints

### 8.5 Infrastructure
- **Keycloak** for identity and access management
- **Redis** for caching and task queue
- **MinIO** for object storage (documents)
- **Docker Compose** for local development
- **Helm** for Kubernetes/OpenShift deployment

---

## 9. Fair Lending & Compliance

### 9.1 Regulatory Framework

MortgageAI must comply with:
- **Equal Credit Opportunity Act (ECOA)**: Cannot discriminate based on race, color, religion, national origin, sex, marital status, age
- **Fair Housing Act**: Prohibits discrimination in housing-related transactions
- **Home Mortgage Disclosure Act (HMDA)**: Reporting requirements
- **Truth in Lending Act (TILA)**: Disclosure requirements

### 9.2 Compliance Safeguards

- **Protected characteristic isolation**: AI agents never receive race, religion, or other protected characteristics
- **Disparate impact monitoring**: Regular analysis of decision patterns across demographic groups
- **Adverse action notices**: Automated generation of legally compliant denial explanations
- **Audit trail**: Complete logging of all AI reasoning and human decisions
- **Bias testing**: Regular bias audits of AI model outputs
- **Regulatory Compliance Agent**: Dedicated agent that reviews every decision for compliance

### 9.3 Transparency

- Every decision includes a complete chain of reasoning
- Applicants receive specific, actionable reasons for adverse decisions
- Loan servicers can drill into any factor to see underlying data and AI reasoning
- All overrides require documented justification

---

## 10. Security Considerations

- **Data Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Document Security**: Encrypted storage, access-controlled retrieval, automatic expiry
- **PII Handling**: Minimal retention, anonymization for analytics, right to deletion
- **API Security**: JWT tokens via Keycloak, rate limiting, input validation
- **Audit Logging**: Immutable audit trail for all operations
- **LLM Data Privacy**: No PII sent to external LLMs without explicit consent; local LLM option for full data sovereignty

---

## 11. Success Metrics

| Metric | Target |
|--------|--------|
| Application completion rate | > 80% |
| Average time from submission to AI decision | < 5 minutes |
| Average time from submission to final decision | < 24 hours |
| AI recommendation accuracy (vs. servicer agreement) | > 85% |
| Fair lending compliance (no disparate impact) | 100% |
| Applicant satisfaction score | > 4.2/5 |
| Loan servicer time saved per application | > 60% |

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - a standard for connecting AI agents with tools and data sources |
| **LLM** | Large Language Model - AI model used for natural language understanding and generation |
| **DTI** | Debt-to-Income ratio - total monthly debt payments divided by gross monthly income |
| **LTV** | Loan-to-Value ratio - loan amount divided by property appraised value |
| **ECOA** | Equal Credit Opportunity Act - federal law prohibiting credit discrimination |
| **ITIN** | Individual Taxpayer Identification Number - issued to individuals not eligible for SSN |
| **OCR** | Optical Character Recognition - technology to extract text from images/documents |
| **RBAC** | Role-Based Access Control - access management based on user roles |
| **Adverse Action** | A negative decision on a credit application, requiring specific disclosures |

---

## 13. Out of Scope (v1)

- Loan servicing post-approval (payment tracking, escrow management)
- Secondary market trading
- Multi-language support (English only in v1)
- Mobile native applications (responsive web only)
- Direct credit bureau API integration (manual input in v1, API integration in v2)
- Automated property appraisal ordering
