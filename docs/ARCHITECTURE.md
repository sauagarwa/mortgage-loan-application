# MortgageAI: System Architecture

**Version:** 1.0
**Date:** 2026-02-13

---

## 1. High-Level Architecture

```
                          ┌─────────────────────────────────┐
                          │          Load Balancer           │
                          │      (OpenShift Route/Ingress)   │
                          └──────┬──────────────┬────────────┘
                                 │              │
                    ┌────────────▼──┐    ┌──────▼────────────┐
                    │   Frontend    │    │     Backend API    │
                    │  (React/Vite) │    │    (FastAPI)       │
                    │   Port 3000   │    │    Port 8000       │
                    └───────────────┘    └──────┬────────────┘
                                               │
                    ┌──────────────────────────┬┴──────────────────────┐
                    │                          │                       │
             ┌──────▼──────┐          ┌───────▼───────┐       ┌──────▼──────┐
             │  PostgreSQL │          │    Redis      │       │   MinIO     │
             │  + pgvector │          │  (Cache/Queue)│       │ (Documents) │
             │  Port 5432  │          │  Port 6379    │       │  Port 9000  │
             └─────────────┘          └───────────────┘       └─────────────┘
                                               │
                                      ┌────────▼────────┐
                                      │  Celery Workers  │
                                      │  (AI Processing) │
                                      └────────┬─────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                       ┌──────▼──────┐  ┌──────▼──────┐ ┌──────▼──────┐
                       │   OpenAI    │  │  Anthropic  │ │  Local LLM  │
                       │   API       │  │   API       │ │  (vLLM etc) │
                       └─────────────┘  └─────────────┘ └─────────────┘

                    ┌─────────────────────────────────────────────┐
                    │              Keycloak                       │
                    │     Identity & Access Management            │
                    │              Port 8080                      │
                    └─────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Frontend (packages/ui)

```
packages/ui/src/
├── main.tsx                          # App entry: React + Router + QueryClient + Keycloak
├── auth/
│   ├── keycloak.ts                   # Keycloak instance configuration
│   ├── auth-provider.tsx             # AuthProvider context wrapper
│   └── protected-route.tsx           # Route guard component
├── components/
│   ├── atoms/                        # Base UI primitives (shadcn/ui)
│   │   ├── button/
│   │   ├── card/
│   │   ├── input/
│   │   ├── select/
│   │   ├── textarea/
│   │   ├── dialog/
│   │   ├── table/
│   │   ├── tabs/
│   │   ├── progress/
│   │   ├── badge/
│   │   ├── alert/
│   │   ├── file-upload/
│   │   └── stepper/
│   ├── applicant/                    # Applicant-specific components
│   │   ├── application-form/         # Multi-step loan application form
│   │   ├── document-upload/          # Document upload with preview
│   │   ├── loan-selector/            # Loan product comparison & selection
│   │   ├── application-status/       # Application tracking dashboard
│   │   └── decision-display/         # AI decision with explanation
│   ├── servicer/                     # Loan servicer components
│   │   ├── application-queue/        # Pending applications list
│   │   ├── risk-assessment/          # AI risk breakdown display
│   │   ├── document-viewer/          # Document review interface
│   │   ├── decision-panel/           # Approve/deny/request-info panel
│   │   └── analytics-dashboard/      # Portfolio analytics
│   ├── shared/                       # Cross-role components
│   │   ├── header/
│   │   ├── footer/
│   │   ├── sidebar/
│   │   └── notification-center/
│   └── charts/                       # Data visualization
│       ├── risk-radar/               # Radar chart for risk dimensions
│       └── score-gauge/              # Gauge chart for risk score
├── hooks/
│   ├── auth.ts                       # useAuth, useUser, useRoles
│   ├── applications.ts              # useApplications, useApplication
│   ├── documents.ts                  # useDocuments, useUpload
│   ├── risk-assessment.ts           # useRiskAssessment
│   ├── loans.ts                      # useLoanProducts
│   └── decisions.ts                  # useDecision, useApprove, useDeny
├── services/
│   ├── api-client.ts                 # Axios/fetch with Keycloak token injection
│   ├── applications.ts              # Application CRUD API calls
│   ├── documents.ts                  # Document upload/download API calls
│   ├── risk-assessment.ts           # Risk assessment API calls
│   ├── loans.ts                      # Loan products API calls
│   └── decisions.ts                  # Decision API calls
├── schemas/
│   ├── application.ts               # Application Zod schemas
│   ├── document.ts                   # Document Zod schemas
│   ├── risk-assessment.ts           # Risk assessment Zod schemas
│   ├── loan.ts                       # Loan product Zod schemas
│   └── decision.ts                   # Decision Zod schemas
├── routes/
│   ├── __root.tsx                    # Root layout with auth guard
│   ├── index.tsx                     # Landing / login redirect
│   ├── dashboard/
│   │   └── index.tsx                 # Role-based dashboard redirect
│   ├── apply/
│   │   ├── index.tsx                 # Loan selection
│   │   └── $loanType.tsx            # Application form for loan type
│   ├── applications/
│   │   ├── index.tsx                 # My applications list
│   │   └── $applicationId.tsx       # Application detail
│   ├── servicer/
│   │   ├── index.tsx                 # Servicer dashboard / queue
│   │   ├── $applicationId.tsx       # Application review
│   │   └── analytics.tsx             # Portfolio analytics
│   └── admin/
│       ├── index.tsx                 # Admin dashboard
│       ├── settings.tsx              # System settings
│       └── users.tsx                 # User management
└── styles/
    └── globals.css                   # Tailwind + custom design tokens
```

### 2.2 Backend API (packages/api)

```
packages/api/src/
├── main.py                           # FastAPI app, middleware, router registration
├── core/
│   ├── config.py                     # Pydantic Settings (env vars)
│   ├── security.py                   # Keycloak JWT validation, RBAC decorators
│   ├── dependencies.py               # Shared FastAPI dependencies
│   └── exceptions.py                 # Custom exception handlers
├── routes/
│   ├── health.py                     # Health check endpoints
│   ├── auth.py                       # Auth callback, token exchange
│   ├── applications.py              # CRUD for loan applications
│   ├── documents.py                  # Document upload/download/delete
│   ├── loans.py                      # Loan products catalog
│   ├── risk_assessment.py           # Trigger and retrieve risk assessments
│   ├── decisions.py                  # Final decision endpoints
│   └── admin.py                      # Admin configuration endpoints
├── schemas/
│   ├── application.py               # Application request/response models
│   ├── document.py                   # Document metadata models
│   ├── risk_assessment.py           # Risk assessment models
│   ├── loan.py                       # Loan product models
│   ├── decision.py                   # Decision models
│   └── common.py                     # Shared schemas (pagination, errors)
├── models/                           # Re-exports from db package
├── services/
│   ├── application_service.py       # Application business logic
│   ├── document_service.py          # Document storage & retrieval
│   ├── risk_assessment_service.py   # Orchestrates MCP agent pipeline
│   ├── decision_service.py          # Decision workflow logic
│   ├── notification_service.py      # Email/notification dispatch
│   └── llm_gateway.py               # Multi-provider LLM client
├── agents/                           # MCP Agent definitions
│   ├── base.py                       # Base agent class with MCP protocol
│   ├── credit_analysis.py           # Credit Analysis Agent
│   ├── employment_verification.py   # Employment Verification Agent
│   ├── document_processing.py       # Document Processing Agent
│   ├── financial_health.py          # Financial Health Agent
│   ├── property_valuation.py        # Property Valuation Agent
│   ├── applicant_profile.py         # Applicant Profile Agent
│   ├── regulatory_compliance.py     # Regulatory Compliance Agent
│   ├── risk_aggregation.py          # Risk Aggregation Agent
│   └── tools/                        # MCP Tools used by agents
│       ├── credit_tools.py          # Credit data retrieval tools
│       ├── financial_tools.py       # Financial calculation tools
│       ├── document_tools.py        # OCR and extraction tools
│       ├── property_tools.py        # Property data tools
│       └── compliance_tools.py      # Regulatory check tools
├── tasks/
│   ├── celery_app.py                # Celery configuration
│   ├── risk_assessment_task.py      # Async risk assessment processing
│   └── document_processing_task.py  # Async document OCR processing
└── admin.py                          # SQLAdmin configuration
```

### 2.3 Database (packages/db)

```
packages/db/
├── src/db/
│   ├── database.py                   # Engine, session factory, base
│   ├── models.py                     # All SQLAlchemy models
│   └── __init__.py                   # Public exports
├── alembic/
│   ├── versions/                     # Migration files
│   ├── env.py                        # Alembic config
│   └── script.py.mako               # Migration template
└── seeds/
    ├── loan_products.py              # Seed data for loan types
    └── test_data.py                  # Development test data
```

---

## 3. Data Flow Architecture

### 3.1 Application Submission Flow

```
Applicant Browser                   API Server                  Database
      │                                │                           │
      │  POST /api/applications        │                           │
      │  {personal_info, financial,    │                           │
      │   loan_type, property}         │                           │
      ├───────────────────────────────>│                           │
      │                                │  Validate & store         │
      │                                ├──────────────────────────>│
      │                                │            application_id │
      │                                │<──────────────────────────┤
      │                                │                           │
      │                                │  Dispatch to Celery       │
      │                                ├────────┐                  │
      │    202 Accepted                │        │ task_id          │
      │    {application_id, status:    │        ▼                  │
      │     "submitted"}               │   ┌─────────┐            │
      │<───────────────────────────────┤   │  Redis   │            │
      │                                │   │  Queue   │            │
      │                                │   └────┬────┘            │
      │                                │        │                  │
      │                                │        ▼                  │
      │                                │   ┌─────────┐            │
      │                                │   │ Celery   │            │
      │                                │   │ Worker   │            │
      │                                │   └────┬────┘            │
      │                                │        │                  │
      │                                │        ▼                  │
      │                                │   MCP Agent Pipeline     │
      │                                │   (see section 4)         │
```

### 3.2 Document Upload Flow

```
Applicant Browser                   API Server              MinIO          Celery
      │                                │                      │               │
      │  POST /api/documents           │                      │               │
      │  multipart/form-data           │                      │               │
      ├───────────────────────────────>│                      │               │
      │                                │  Store file           │               │
      │                                ├─────────────────────>│               │
      │                                │         object_key    │               │
      │                                │<─────────────────────┤               │
      │                                │  Save metadata to DB  │               │
      │                                │                      │               │
      │                                │  Queue OCR task       │               │
      │                                ├──────────────────────────────────────>│
      │   201 Created                  │                      │               │
      │   {document_id, status:        │                      │               │
      │    "processing"}               │                      │               │
      │<───────────────────────────────┤                      │               │
      │                                │                      │  OCR Process  │
      │                                │                      │<──────────────┤
      │                                │                      │  Get file     │
      │                                │   Update DB with      │               │
      │                                │   extracted data      │               │
      │                                │<─────────────────────────────────────┤
```

### 3.3 Risk Assessment Flow

```
Celery Worker
      │
      │  Load application data from DB
      │
      ▼
┌─────────────────────────────┐
│   Document Processing Agent │──── Extract structured data from uploaded docs
└────────────┬────────────────┘
             │
             ▼ (fan-out: parallel execution)
┌────────────┴───────────────────────────────────────────────────────────┐
│                                                                        │
▼              ▼                ▼               ▼              ▼         │
┌──────┐  ┌────────┐   ┌───────────┐   ┌────────┐   ┌──────────┐      │
│Credit│  │Employ- │   │ Financial │   │Property│   │ Applicant│      │
│Anal. │  │ment    │   │  Health   │   │Valua-  │   │ Profile  │      │
│Agent │  │Verif.  │   │  Agent    │   │tion    │   │  Agent   │      │
│      │  │Agent   │   │           │   │Agent   │   │          │      │
└──┬───┘  └──┬─────┘   └────┬──────┘   └──┬─────┘   └────┬─────┘      │
   │         │              │             │              │              │
   │    Agent Results (structured JSON)    │              │              │
   └─────────┴──────────────┴─────────────┴──────────────┘              │
                            │                                           │
                            ▼                                           │
                  ┌──────────────────┐                                  │
                  │   Regulatory     │──── Check fair lending compliance│
                  │   Compliance     │                                  │
                  │   Agent          │                                  │
                  └────────┬─────────┘                                  │
                           │                                           │
                           ▼                                           │
                  ┌──────────────────┐                                  │
                  │ Risk Aggregation │──── Synthesize all agent outputs │
                  │ Agent            │──── Generate composite score     │
                  │                  │──── Write natural language       │
                  │                  │     explanation                  │
                  └────────┬─────────┘                                  │
                           │                                           │
                           ▼                                           │
                    Store results in DB                                 │
                    Notify loan servicer                                │
                    Update application status                           │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 4. MCP Agent Architecture

### 4.1 MCP Protocol Integration

Each agent follows the Model Context Protocol standard:

```
┌──────────────────────────────────────────────┐
│                  MCP Host                     │
│            (Risk Assessment Service)          │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Agent 1 │  │  Agent 2 │  │  Agent N │   │
│  │  (MCP    │  │  (MCP    │  │  (MCP    │   │
│  │  Client) │  │  Client) │  │  Client) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │         │
│       ▼              ▼              ▼         │
│  ┌──────────────────────────────────────┐     │
│  │         MCP Server (per agent)       │     │
│  │  ┌──────┐  ┌──────────┐  ┌───────┐  │     │
│  │  │Tools │  │ Resources│  │Prompts│  │     │
│  │  └──────┘  └──────────┘  └───────┘  │     │
│  └──────────────────────────────────────┘     │
└──────────────────────────────────────────────┘
```

### 4.2 Agent Communication Pattern

```python
# Each agent exposes:
# 1. Tools - functions the LLM can call
# 2. Resources - data sources the LLM can read
# 3. Prompts - pre-defined prompt templates

class MCPAgent:
    """Base MCP agent with tool definitions and LLM interaction."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = LLMGateway(llm_config)
        self.tools = self.register_tools()
        self.resources = self.register_resources()

    async def analyze(self, context: ApplicationContext) -> AgentResult:
        """Run analysis using LLM with registered tools."""
        messages = self.build_prompt(context)
        result = await self.llm.chat_with_tools(messages, self.tools)
        return self.parse_result(result)
```

### 4.3 LLM Gateway Architecture

```
┌────────────────────────────────────────────────┐
│              LLM Gateway Service               │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │          Provider Registry               │  │
│  │  ┌────────┐ ┌─────────┐ ┌────────────┐  │  │
│  │  │ OpenAI │ │Anthropic│ │   Local     │  │  │
│  │  │Provider│ │Provider │ │  Provider   │  │  │
│  │  └────┬───┘ └────┬────┘ └─────┬──────┘  │  │
│  │       │          │            │          │  │
│  │       ▼          ▼            ▼          │  │
│  │  ┌──────────────────────────────────┐    │  │
│  │  │     Unified Chat Interface       │    │  │
│  │  │  - chat_completion()             │    │  │
│  │  │  - chat_with_tools()             │    │  │
│  │  │  - streaming_chat()              │    │  │
│  │  └──────────────────────────────────┘    │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │          Configuration                   │  │
│  │  - provider: openai|anthropic|local      │  │
│  │  - base_url: https://... (or local)      │  │
│  │  - api_key: sk-... (optional for local)  │  │
│  │  - model: gpt-4o|claude-sonnet|custom    │  │
│  │  - max_tokens: 4096                      │  │
│  │  - temperature: 0.1                      │  │
│  │  - rate_limit: 60 req/min                │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

---

## 5. Authentication & Authorization Architecture

### 5.1 Keycloak Integration

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────>│   Keycloak   │────>│   FastAPI     │
│              │     │   Server     │     │   Backend     │
│  keycloak-js │     │              │     │              │
│  adapter     │     │  Realm:      │     │  JWT          │
│              │     │  mortgage-ai │     │  Validation   │
│  Stores JWT  │     │              │     │              │
│  in memory   │     │  Clients:    │     │  RBAC         │
│              │     │  - ui-client │     │  Middleware    │
│  Refreshes   │     │  - api-client│     │              │
│  tokens      │     │              │     │  Role-based   │
│              │     │  Roles:      │     │  Endpoints    │
│  Sends JWT   │     │  - applicant │     │              │
│  in headers  │     │  - servicer  │     │              │
│              │     │  - admin     │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 5.2 Authentication Flow

```
1. User visits app
       │
       ▼
2. Keycloak JS checks for session
       │
       ├── Session exists → Load user, proceed
       │
       └── No session → Redirect to Keycloak login
                │
                ▼
         3. User authenticates
            (username/password or social)
                │
                ▼
         4. Keycloak redirects back with auth code
                │
                ▼
         5. Frontend exchanges code for tokens
            (access_token + refresh_token)
                │
                ▼
         6. Frontend stores tokens in memory
            Attaches access_token to all API requests
            as Authorization: Bearer <token>
                │
                ▼
         7. Backend validates JWT signature
            Extracts user info and roles
            Enforces RBAC on each endpoint
```

### 5.3 Role-Based Access Control

```python
# Backend RBAC decorator pattern
@router.get("/applications")
@require_role(["loan_servicer", "admin"])
async def list_all_applications(...):
    """Only loan servicers and admins can see all applications."""

@router.get("/applications/mine")
@require_role(["applicant"])
async def list_my_applications(user: User = Depends(get_current_user)):
    """Applicants can only see their own applications."""

@router.post("/applications/{id}/approve")
@require_role(["loan_servicer"])
async def approve_application(...):
    """Only loan servicers can approve applications."""
```

---

## 6. Deployment Architecture

### 6.1 Local Development (Docker Compose)

```yaml
services:
  ui:              # React dev server (port 3000)
  api:             # FastAPI server (port 8000)
  db:              # PostgreSQL 16 + pgvector (port 5432)
  redis:           # Redis (port 6379)
  minio:           # MinIO object storage (port 9000)
  keycloak:        # Keycloak IAM (port 8080)
  keycloak-db:     # PostgreSQL for Keycloak (port 5433)
  celery-worker:   # Celery worker for async tasks
  celery-beat:     # Celery beat scheduler
```

### 6.2 Production (OpenShift/Kubernetes)

```
┌─────────────────────────────────────────────────────────┐
│                    OpenShift Cluster                     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │  UI Pod(s)  │  │  API Pod(s) │  │ Worker Pod(s)│   │
│  │  (Nginx +   │  │  (Uvicorn + │  │ (Celery      │   │
│  │   React)    │  │   FastAPI)  │  │  Workers)    │   │
│  │  replicas:2 │  │  replicas:2 │  │  replicas:2  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘   │
│         │                │                │            │
│  ┌──────▼────────────────▼────────────────▼───────┐   │
│  │              Service Mesh / Network              │   │
│  └──────┬────────────────┬────────────────┬───────┘   │
│         │                │                │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼───────┐  │
│  │ PostgreSQL  │  │    Redis    │  │    MinIO     │  │
│  │ (StatefulSet│  │ (StatefulSet│  │ (StatefulSet │  │
│  │  + PVC)     │  │  + PVC)     │  │  + PVC)      │  │
│  └─────────────┘  └─────────────┘  └──────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Keycloak (Operator-managed)         │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │  Route: UI   │  │  Route: API  │                   │
│  │  TLS Edge    │  │  TLS Edge    │                   │
│  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

### 7.1 Network Security

```
Internet ──> WAF ──> Load Balancer ──> TLS Termination ──> Internal Services
                                                                │
                                              All internal traffic encrypted
                                              Network policies enforce isolation
                                              Service-to-service mTLS (optional)
```

### 7.2 Data Security Layers

| Layer | Protection |
|-------|-----------|
| Transport | TLS 1.3 for all external/internal communication |
| Application | JWT token validation, RBAC, input sanitization |
| Storage | AES-256 encryption at rest (database, MinIO) |
| Documents | Encrypted storage, signed download URLs (time-limited) |
| PII | Field-level encryption for SSN, DOB; data masking in logs |
| LLM | PII scrubbing before sending to external LLMs; local LLM option |
| Audit | Immutable audit log for all state-changing operations |

### 7.3 Document Security

```
Upload:
  Client ──[TLS]──> API ──[encrypt]──> MinIO (encrypted bucket)
                      │
                      └──> DB (metadata only, no file content)

Download:
  Client ──[TLS]──> API ──[auth check]──> MinIO ──[pre-signed URL]──> Client
                                              │
                                          URL expires in 15 minutes
                                          Scoped to specific document
```

---

## 8. Monitoring & Observability

```
┌─────────────────────────────────────────────┐
│              Observability Stack             │
│                                             │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Metrics   │  │  Logs    │  │ Traces   │ │
│  │(Prometheus│  │(EFK/Loki)│  │(Jaeger/  │ │
│  │ /Grafana) │  │          │  │ Tempo)   │ │
│  └───────────┘  └──────────┘  └──────────┘ │
│                                             │
│  Key Metrics:                               │
│  - Request latency (p50, p95, p99)          │
│  - AI agent processing time                  │
│  - LLM token usage per provider             │
│  - Application funnel conversion rates       │
│  - Error rates by endpoint                   │
│  - Document processing queue depth           │
│  - Active users by role                      │
└─────────────────────────────────────────────┘
```

---

## 9. Technology Decision Records

### 9.1 Why MCP for AI Agents?

**Decision**: Use Model Context Protocol (MCP) for agent orchestration instead of raw LLM calls or LangChain agents.

**Rationale**:
- Standard protocol for tool/resource/prompt management
- Agent isolation - each agent has its own tools and context
- Provider-agnostic - works with any LLM backend
- Composable - agents can be added/removed without changing orchestration
- Observable - standard protocol enables consistent logging and monitoring

### 9.2 Why Celery for Async Processing?

**Decision**: Use Celery with Redis for asynchronous AI processing instead of FastAPI background tasks.

**Rationale**:
- AI analysis takes 30-120 seconds per application
- Need separate worker scaling from API servers
- Task retry and dead-letter queue support
- Progress tracking via task state
- Horizontal scaling of workers independent of API

### 9.3 Why MinIO for Documents?

**Decision**: Use MinIO for document storage instead of filesystem or database BLOBs.

**Rationale**:
- S3-compatible API (portable to AWS S3, GCS)
- Encryption at rest built-in
- Pre-signed URLs for secure, time-limited access
- Horizontal scaling and replication
- Runs locally and in Kubernetes

### 9.4 Why Keycloak for Auth?

**Decision**: Use Keycloak instead of custom auth or Auth0/Okta.

**Rationale**:
- Open source, self-hosted (data sovereignty)
- Enterprise features (RBAC, federation, MFA, social login)
- OpenShift Keycloak Operator for easy deployment
- Standard OIDC/OAuth 2.0 (portable)
- Admin console for user/role management
