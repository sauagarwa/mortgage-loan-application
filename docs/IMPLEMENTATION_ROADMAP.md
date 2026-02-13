# MortgageAI: Implementation Roadmap

**Version:** 1.0
**Date:** 2026-02-13

---

## Phase 1: Foundation & Infrastructure

### 1.1 Project Setup
- [x] Initialize from ai-quickstart-template
- [ ] Update project name/branding in package.json, pyproject.toml, Helm chart
- [ ] Configure environment variables for all new services
- [ ] Update compose.yml with new services (Redis, MinIO, Keycloak, Celery)

### 1.2 Database Schema
- [ ] Create SQLAlchemy models for all tables (user, loan_product, application, document, risk_assessment, risk_dimension_score, decision, info_request, llm_config, audit_log, notification)
- [ ] Generate Alembic migrations
- [ ] Create seed data (loan products, default LLM configs)
- [ ] Test database connectivity and migrations

### 1.3 Authentication (Keycloak)
- [ ] Add Keycloak container to compose.yml
- [ ] Configure Keycloak realm (mortgage-ai) with roles
- [ ] Implement backend JWT validation middleware
- [ ] Implement frontend Keycloak JS adapter
- [ ] Create RBAC decorator for API routes
- [ ] Test login/logout/token refresh flows

---

## Phase 2: Core API & Frontend Shell

### 2.1 Backend API - Core Endpoints
- [ ] Application CRUD endpoints (create, read, update, list, submit)
- [ ] Loan products endpoints (list, detail, eligibility check)
- [ ] Document upload/download/delete endpoints
- [ ] User profile endpoints
- [ ] Health check endpoints (extended with all services)

### 2.2 Frontend - Application Shell
- [ ] Keycloak auth integration (login, logout, token management)
- [ ] Protected route guards
- [ ] Role-based navigation (applicant vs. servicer vs. admin)
- [ ] Layout components (sidebar, header with user menu)
- [ ] Theme setup (light/dark mode)

### 2.3 Frontend - Applicant Flows
- [ ] Loan products browse page
- [ ] Eligibility pre-check component
- [ ] Multi-step application form (6 steps)
- [ ] Form validation with Zod
- [ ] Auto-save draft functionality
- [ ] Document upload component (drag-and-drop)
- [ ] Application review & submit page
- [ ] My applications list/dashboard

### 2.4 Frontend - Servicer Flows
- [ ] Application queue table with sorting/filtering
- [ ] Dashboard statistics cards
- [ ] Application review page (data + risk assessment)
- [ ] Decision panel (approve/deny/conditional/request info)

---

## Phase 3: Document Processing & Storage

### 3.1 MinIO Integration
- [ ] Add MinIO container to compose.yml
- [ ] Implement document storage service (upload, download, delete)
- [ ] Pre-signed URL generation for secure downloads
- [ ] Bucket policies and encryption configuration

### 3.2 Async Task Processing
- [ ] Add Redis container to compose.yml
- [ ] Configure Celery with Redis broker
- [ ] Implement document processing task
- [ ] Implement risk assessment task
- [ ] Worker health monitoring

### 3.3 Document OCR
- [ ] Integrate OCR library (Tesseract or cloud API)
- [ ] Build extraction pipelines per document type
- [ ] Structured data extraction (pay stubs, W-2, tax returns, bank statements)
- [ ] Extraction confidence scoring
- [ ] Cross-document validation

---

## Phase 4: AI/MCP Agent Implementation

### 4.1 LLM Gateway
- [ ] Implement multi-provider LLM gateway
- [ ] OpenAI provider adapter
- [ ] Anthropic provider adapter
- [ ] Local/OpenAI-compatible provider adapter
- [ ] Provider health check and fallback logic
- [ ] Token usage tracking
- [ ] Rate limiting per provider

### 4.2 MCP Agent Framework
- [ ] Base MCP agent class with tool registration
- [ ] Agent configuration (model, temperature, per agent)
- [ ] Agent result schema (score, factors, explanation)
- [ ] Progress reporting via WebSocket

### 4.3 Individual Agents
- [ ] Document Processing Agent
- [ ] Credit Analysis Agent
- [ ] Employment Verification Agent
- [ ] Financial Health Agent
- [ ] Property Valuation Agent
- [ ] Applicant Profile Agent
- [ ] Regulatory Compliance Agent
- [ ] Risk Aggregation Agent

### 4.4 Agent Pipeline Orchestration
- [ ] Sequential + parallel execution pipeline
- [ ] Error handling and retry logic
- [ ] Progress tracking and WebSocket updates
- [ ] Result storage in database
- [ ] Application status transitions

---

## Phase 5: Decision Workflow & Notifications

### 5.1 Decision Endpoints
- [ ] Approve endpoint with conditions
- [ ] Deny endpoint with adverse action reasons
- [ ] Conditional approve endpoint
- [ ] Request additional info endpoint
- [ ] Override AI recommendation workflow

### 5.2 Notifications
- [ ] In-app notification system
- [ ] WebSocket real-time notifications
- [ ] Email notification integration (optional)
- [ ] Notification preferences

### 5.3 Audit Trail
- [ ] Audit log middleware (auto-log all mutations)
- [ ] Audit log query API
- [ ] Admin audit log viewer

---

## Phase 6: Admin & Polish

### 6.1 Admin Panel
- [ ] LLM provider configuration UI
- [ ] User management UI
- [ ] System health dashboard
- [ ] Audit log viewer with search/filter

### 6.2 Analytics
- [ ] Servicer analytics dashboard (approval rates, processing times)
- [ ] Risk distribution charts
- [ ] Override tracking and reporting

### 6.3 Testing
- [ ] Unit tests for all API endpoints
- [ ] Unit tests for all MCP agents (with mocked LLM)
- [ ] Integration tests for risk assessment pipeline
- [ ] Frontend component tests
- [ ] E2E tests for critical workflows

### 6.4 Deployment
- [ ] Update Helm charts for all new services
- [ ] Container images for API, UI, Celery workers
- [ ] Production configuration guide
- [ ] Security review checklist

---

## Technology Dependencies Summary

| Component | Technology | Added In |
|-----------|-----------|----------|
| Frontend | React 19 + Vite + TanStack | Template |
| Backend | FastAPI + SQLAlchemy | Template |
| Database | PostgreSQL 16 + pgvector | Template |
| Auth | Keycloak | Phase 1 |
| Cache/Queue | Redis | Phase 3 |
| Object Storage | MinIO | Phase 3 |
| Task Queue | Celery | Phase 3 |
| OCR | Tesseract / Cloud OCR | Phase 3 |
| LLM Providers | OpenAI, Anthropic, Local | Phase 4 |
| MCP Framework | Custom MCP agents | Phase 4 |
