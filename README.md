# MortgageAI: Intelligent Mortgage Loan Origination & Approval Platform

An AI-powered mortgage loan origination and approval platform that delivers holistic, fair, and explainable lending decisions using multiple AI agents via the Model Context Protocol (MCP).

## Key Features

- **Multi-dimensional risk assessment** - Goes beyond credit scores to evaluate employment stability, financial behavior, credit trajectory, and contextual factors
- **MCP AI agents** - 8 specialized agents (Credit Analysis, Employment Verification, Financial Health, Property Valuation, Applicant Profile, Document Processing, Regulatory Compliance, Risk Aggregation)
- **Explainable decisions** - Every AI recommendation includes detailed reasoning, positive factors, risk factors, and mitigating factors
- **Human-in-the-loop** - Loan servicers review AI assessments and make final approval decisions
- **Fair lending** - Built-in compliance with ECOA and Fair Housing Act; dedicated regulatory compliance agent
- **Multi-LLM support** - OpenAI, Anthropic, or self-hosted OpenAI-compatible models with configurable base URL
- **Keycloak authentication** - Role-based access (applicant, loan servicer, admin) with self-registration
- **Document processing** - Upload, OCR, and AI-powered data extraction from pay stubs, W-2s, tax returns, bank statements

## Documentation

| Document | Description |
|----------|-------------|
| [Concept Document](docs/CONCEPT.md) | Vision, problem statement, capabilities, and workflows |
| [Architecture](docs/ARCHITECTURE.md) | System architecture, component design, data flows |
| [API Specification](docs/API_SPECIFICATION.md) | REST API endpoints, schemas, WebSocket specs |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Table definitions, relationships, migration strategy |
| [MCP Agents](docs/MCP_AGENTS.md) | AI agent design, tools, prompts, orchestration |
| [User Stories](docs/USER_STORIES.md) | User stories, personas, workflows, acceptance criteria |
| [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) | Phased implementation plan |

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐
│   React/Vite    │───>│   FastAPI     │───>│  PostgreSQL  │
│   Frontend      │    │   Backend     │    │  + pgvector  │
│   + Keycloak JS │    │   + Celery    │    └──────────────┘
└─────────────────┘    │   Workers     │
                       └──────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼────┐   ┌─────▼────┐   ┌──────▼─────┐
        │  OpenAI  │   │Anthropic │   │ Local LLM  │
        │  API     │   │  API     │   │ (vLLM etc) │
        └──────────┘   └──────────┘   └────────────┘

   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Keycloak │   │  Redis   │   │  MinIO   │
   │  (Auth)  │   │ (Queue)  │   │ (Docs)   │
   └──────────┘   └──────────┘   └──────────┘
```

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, TanStack Router/Query, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic v2, Celery
- **Database**: PostgreSQL 16 + pgvector
- **AI**: MCP agents, multi-provider LLM gateway
- **Auth**: Keycloak (OIDC/OAuth 2.0)
- **Storage**: MinIO (S3-compatible)
- **Infrastructure**: Docker Compose (dev), Helm/OpenShift (prod)

## Project Structure

```
mortgage-application/
├── docs/                 # Project documentation
├── packages/
│   ├── ui/              # React frontend application
│   ├── api/             # FastAPI backend service
│   │   └── src/
│   │       ├── agents/  # MCP agent definitions
│   │       ├── routes/  # API endpoints
│   │       ├── services/# Business logic
│   │       └── tasks/   # Celery async tasks
│   ├── db/              # Database models and migrations
│   └── configs/         # Shared linting/formatting configs
├── deploy/
│   └── helm/            # Helm charts for OpenShift/K8s
├── compose.yml          # Local dev services
├── Makefile             # Common commands
├── turbo.json           # Turborepo configuration
└── package.json         # Root package configuration
```

## Quick Start

### Prerequisites
- Node.js 18+
- pnpm 9+
- Python 3.11+
- uv (Python package manager)
- Podman/Docker and podman-compose/docker-compose

### Development

```bash
# Install all dependencies
make setup

# Start infrastructure services (DB, Redis, MinIO, Keycloak)
make db-start

# Run database migrations
make db-upgrade

# Start development servers (UI + API)
make dev
```

### Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Server | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Keycloak Admin | http://localhost:8080 |
| MinIO Console | http://localhost:9001 |
| Storybook | http://localhost:6006 |

## User Roles

| Role | Description |
|------|-------------|
| **Applicant** | Creates account, applies for loans, uploads documents, views decisions |
| **Loan Servicer** | Reviews applications with AI assessments, makes final approval decisions |
| **Admin** | Configures LLM providers, manages users, views audit logs |

## AI Risk Assessment Dimensions

| Dimension | Weight | Agent |
|-----------|--------|-------|
| Credit History & Trajectory | 20% | Credit Analysis |
| Employment & Income Stability | 20% | Employment Verification |
| Financial Health (DTI, Assets) | 15% | Financial Health |
| Property & Collateral | 15% | Property Valuation |
| Applicant Profile | 10% | Applicant Profile |
| Behavioral Patterns | 10% | Financial Health |
| Regulatory Compliance | 10% | Regulatory Compliance |

---

Built on [AI QuickStart Template](https://github.com/rh-ai-quickstart/ai-quickstart-template)
