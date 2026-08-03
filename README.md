<div align="center">

# 🪬 Sentinel AI Governance Platform
**Enterprise AI Governance, Observability & Graduated Autonomy Engine**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Gemini LLM](https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=googlebard)](https://deepmind.google/technologies/gemini/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[Live Deployments](#live-production-deployments) • [Overview](#overview) • [Key Features](#key-features) • [Tech Stack](#tech-stack) • [Repository Structure](#repository-structure) • [Getting Started](#getting-started) • [Deployment](#deployment) • [License](#license)

</div>

---

## 🚀 Live Production Deployments
- **Web App**: [https://sentinel-ai-governance.onrender.com/](https://sentinel-ai-governance.onrender.com/)

---

## 📖 Overview
**Sentinel AI Governance Platform** is an enterprise-grade "Trust Layer" designed to securely manage, monitor, and audit autonomous AI systems. As organizations scale AI agents into production, the lack of observability and compliance guardrails creates significant operational risk. Sentinel bridges this gap.

Built on a high-performance FastAPI architecture and natively integrated with Google Gemini, this platform provides:

- **Decision Path Explainability**: Complete transparency into *why* an AI agent made a specific choice, generating immutable audit trails for compliance.
- **Graduated Autonomy**: Enforced policy checks and automated Human-in-the-Loop (HITL) workflows when agents attempt high-risk or uncertain operations.
- **Real-time Observability**: Live monitoring of agent behaviors, risk metrics, and system health via bi-directional WebSockets.

By wrapping AI execution in strict, observable guardrails, Sentinel empowers enterprises to confidently deploy autonomous systems while maintaining absolute alignment with corporate and regulatory standards.

## ✨ Core Capabilities

- 🛡️ **Automated Policy Enforcement**: Dynamic rule engines (e.g., `RiskEngine`, `PolicyEngine`) validate agent actions against predefined corporate guidelines before execution.
- 🔍 **Decision Path Explainability**: Comprehensive `audit_logs` record the contextual rationale behind every LLM-generated decision, ensuring full Unit 7 compliance.
- ⚡ **Real-Time Observability**: A bi-directional WebSocket architecture streams live telemetry, risk scoring, and agent state directly to the administrative frontend.
- 🧠 **Graduated Autonomy Models**: Intelligent routing that escalates high-risk, low-confidence decisions to human reviewers via the `/review` portal.
- 🔐 **Enterprise-Grade Security**: JWT-based stateless authentication, bcrypt cryptographic hashing, and rigorous Role-Based Access Control (RBAC).
- 📊 **Executive Dashboards**: Server-side rendered Jinja2 interfaces providing a unified pane of glass for analytics, agent management, and governance overviews.

---

## 🏛️ System Architecture

The Sentinel platform operates through a deeply layered architecture, ensuring that every AI action is validated, governed, and completely auditable.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                               END USER                                      │
│                     Employee / Manager / Administrator                      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PRESENTATION LAYER                              │
│                                                                             │
│  Login │ Dashboard │ AI Assistant │ Governance │ Review Queue │ Analytics   │
│                 Audit Logs │ Settings │ Profile                           │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                    HTTP (REST API) + WebSocket
                                │
                                ▼
═══════════════════════════════════════════════════════════════════════════════
                            FASTAPI BACKEND
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                      │
│                                                                             │
│  Chat API │ Governance API │ Review API │ Dashboard API │ Analytics API     │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
═══════════════════════════════════════════════════════════════════════════════
                            AI PROCESSING LAYER
═══════════════════════════════════════════════════════════════════════════════

                          ┌───────────────────────────┐
                          │         AI Agent          │
                          ├───────────────────────────┤
                          │ • Understand User Prompt  │
                          │ • Call Gemini API         │
                          │ • Generate Action JSON    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │      Planner Agent         │
                          ├────────────────────────────┤
                          │ • Validate Action          │
                          │ • Create Execution Plan    │
                          │ • Build Workflow           │
                          └──────────────┬─────────────┘
                                        │
                                        ▼

═══════════════════════════════════════════════════════════════════════════════
                  GRADUATED AUTONOMY ENGINE (PS-9.1)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Governance Agent                                    │
│                     (Workflow Orchestrator)                                 │
└───────────────┬──────────────────────┬──────────────────────┬───────────────┘
                │                      │                      │
                ▼                      ▼                      ▼

      ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
      │   Risk Engine    │   │  Policy Engine   │   │ Decision Engine  │
      ├──────────────────┤   ├──────────────────┤   ├──────────────────┤
      │ Reversibility    │   │ Business Rules   │   │ Auto             │
      │ Data Scope       │   │ Permissions      │   │ Confirm          │
      │ Regulation       │   │ Restrictions     │   │ Human Review     │
      │ LLM Confidence   │   │ Compliance       │   │ Final Decision   │
      └──────────────────┘   └──────────────────┘   └──────────────────┘
                │                      │                      │
                └──────────────────────┴──────────────────────┘
                                       │
                                       ▼
                           Final Governance Decision

═══════════════════════════════════════════════════════════════════════════════
                          HUMAN OVERSIGHT LAYER
═══════════════════════════════════════════════════════════════════════════════

                                    AUTO
                                      │
                                      │
                                      ▼
                              Execution Service

                                    CONFIRM
                                      │
                                      ▼
                              User Confirmation

                                HUMAN REVIEW
                                      │
                                      ▼
                                  Review Agent
                                      │
                                      ▼
                              Approve / Reject

═══════════════════════════════════════════════════════════════════════════════
                          EXECUTION LAYER
═══════════════════════════════════════════════════════════════════════════════

                        ┌───────────────────────────┐
                        │     Execution Service     │
                        ├───────────────────────────┤
                        │ Validate Request          │
                        │ Execute Transaction       │
                        │ Rollback on Failure       │
                        └─────────────┬─────────────┘
                                      │
                                      ▼

═══════════════════════════════════════════════════════════════════════════════
                          REPOSITORY LAYER
═══════════════════════════════════════════════════════════════════════════════

                              Employee Repository

                              Knowledge Repository

                              Document Repository

                              Review Repository

                              Audit Repository

                              Settings Repository

                                      │
                                      ▼

═══════════════════════════════════════════════════════════════════════════════
                           DATABASE LAYER
═══════════════════════════════════════════════════════════════════════════════

                    PostgreSQL Enterprise Database

                                Employees

                                Knowledge Base

                                Documents

                                Review Queue

                                Audit Logs

                                Settings

                                Learning History

                                    │
                                    ▼

═══════════════════════════════════════════════════════════════════════════════
                     MONITORING & LEARNING LAYER
═══════════════════════════════════════════════════════════════════════════════

                                Audit Service

                                    │

                                    ▼

                            Learning Service

                                    │

                                    ▼

                      Dashboard • Analytics • Reports
```

---

## 🛠 Technology Stack

| Architecture Layer | Core Technologies | Primary Function |
| :--- | :--- | :--- |
| **API Gateway & Routing** | FastAPI, Uvicorn, Pydantic | High-performance, asynchronous REST framework with strict schema validation. |
| **Data Persistence** | PostgreSQL, asyncpg | Highly relational, ACID-compliant data storage utilizing asynchronous drivers. |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic | Advanced data modeling and seamless schema version control. |
| **AI Inference** | Google Gemini (`google-generativeai`) | The core LLM engine driving intelligent decision-making and planning. |
| **Presentation Layer** | HTML5, CSS3, Vanilla JS, Jinja2 | SSR (Server-Side Rendered) templates delivering secure administrative portals. |
| **Identity & Access** | PyJWT, Passlib, bcrypt | Secure credential storage, tokenized auth, and cryptographic hashing. |

---

## 📂 Repository Structure

```text
sentinel-ai-governance/
│
├── app/
│   │
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   │
│   │   ├── api.py
│   │   ├── chat_routes.py
│   │   ├── governance_routes.py
│   │   ├── review_routes.py
│   │   ├── execution_routes.py
│   │   ├── dashboard_routes.py
│   │   ├── analytics_routes.py
│   │   └── settings_routes.py
│   │
│   ├── agents/
│   │   │
│   │   ├── base_agent.py
│   │   ├── ai_agent.py
│   │   ├── planner_agent.py
│   │   ├── governance_agent.py
│   │   └── review_agent.py
│   │
│   ├── engines/
│   │   │
│   │   ├── risk_engine.py
│   │   ├── policy_engine.py
│   │   └── decision_engine.py
│   │
│   ├── services/
│   │   │
│   │   ├── llm_service.py
│   │   ├── execution_service.py
│   │   ├── audit_service.py
│   │   ├── learning_service.py
│   │   ├── dashboard_service.py
│   │   └── websocket_service.py
│   │
│   ├── repositories/
│   │   │
│   │   ├── base_repository.py
│   │   ├── employee_repository.py
│   │   ├── knowledge_repository.py
│   │   ├── document_repository.py
│   │   ├── review_repository.py
│   │   ├── audit_repository.py
│   │   └── settings_repository.py
│   │
│   ├── database/
│   │   │
│   │   ├── database.py
│   │   ├── session.py
│   │   ├── seed.py
│   │   └── init_db.py
│   │
│   ├── models/
│   │   │
│   │   ├── employee.py
│   │   ├── knowledge.py
│   │   ├── document.py
│   │   ├── review.py
│   │   ├── audit.py
│   │   ├── settings.py
│   │   └── action.py
│   │
│   ├── schemas/
│   │   │
│   │   ├── chat_schema.py
│   │   ├── action_schema.py
│   │   ├── governance_schema.py
│   │   ├── review_schema.py
│   │   ├── dashboard_schema.py
│   │   ├── analytics_schema.py
│   │   └── settings_schema.py
│   │
│   ├── prompts/
│   │   │
│   │   ├── system_prompt.py
│   │   ├── planner_prompt.py
│   │   └── governance_prompt.py
│   │
│   ├── core/
│   │   │
│   │   ├── logger.py
│   │   ├── constants.py
│   │   ├── enums.py
│   │   ├── security.py
│   │   ├── websocket_manager.py
│   │   └── exceptions.py
│   │
│   ├── utils/
│   │   │
│   │   ├── parser.py
│   │   ├── formatter.py
│   │   ├── validators.py
│   │   ├── helper.py
│   │   └── response.py
│   │
│   ├── static/
│   │   │
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   ├── dashboard.css
│   │   │   ├── assistant.css
│   │   │   ├── governance.css
│   │   │   ├── review.css
│   │   │   ├── analytics.css
│   │   │   └── settings.css
│   │   │
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   ├── dashboard.js
│   │   │   ├── assistant.js
│   │   │   ├── governance.js
│   │   │   ├── review.js
│   │   │   ├── analytics.js
│   │   │   ├── settings.js
│   │   │   ├── websocket.js
│   │   │   └── api.js
│   │   │
│   │   ├── icons/
│   │   ├── images/
│   │   └── animations/
│   │
│   ├── templates/
│   │   │
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── assistant.html
│   │   ├── governance.html
│   │   ├── review.html
│   │   ├── analytics.html
│   │   ├── settings.html
│   │   ├── profile.html
│   │   └── components/
│   │       ├── navbar.html
│   │       ├── sidebar.html
│   │       ├── footer.html
│   │       ├── modal.html
│   │       ├── loader.html
│   │       ├── toast.html
│   │       ├── workflow.html
│   │       ├── risk_card.html
│   │       └── review_card.html
│   │
│   └── websocket/
│       └── events.py
│
├── tests/
│   ├── test_agents.py
│   ├── test_engines.py
│   ├── test_services.py
│   ├── test_api.py
│   └── test_database.py
│
├── mock_data/
│   ├── employees.csv
│   ├── knowledge_base.csv
│   ├── documents.csv
│   ├── review_queue.csv
│   ├── audit_logs.csv
│   └── settings.json
│
├── requirements.txt
├── .env
├── README.md
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Getting Started

> [!IMPORTANT]  
> Ensure you have **Python 3.11+** installed and a **PostgreSQL** instance running before beginning the local setup.

### 1. Repository Initialization
Clone the repository and isolate dependencies within a virtual environment:

```bash
git clone https://github.com/your-org/sentinel-ai-governance.git
cd sentinel-ai-governance

# Initialize and activate the virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows users: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Environment Configuration
The platform relies heavily on environment variables for security and configuration. Create a `.env` file at the repository root:

```ini
# Application Settings
APP_NAME="Sentinel AI Governance"
APP_VERSION="1.0.0"
DEBUG=true
PORT=8000
HOST="0.0.0.0"

# Database Configuration
# Format: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/sentinel_db"

# Security Credentials
SECRET_KEY="<generate-a-secure-random-string>"
JWT_SECRET="<generate-a-secure-jwt-secret>"

# Artificial Intelligence
GEMINI_API_KEY="<your-google-gemini-api-key>"
```

### 3. Database Migration & Seeding
Synchronize your local PostgreSQL instance with the SQLAlchemy models, then optionally seed it with mock data for testing:
```bash
alembic upgrade head
```

### 4. Application Launch
Start the highly-concurrent Uvicorn server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- 🖥️ **Administrator Console**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- 📚 **Swagger API Reference**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- 🩺 **System Health**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Deployment Architecture

The Sentinel platform is container-native and designed to run anywhere.

### Docker Infrastructure
A robust `Dockerfile` and `docker-compose.yml` are provided for immediate containerized deployment (ideal for AWS EC2, ECS, or GCP).

```bash
# Build the application image
docker build -t sentinel-ai-governance .

# Launch as a background daemon
docker run -d -p 8000:8000 --env-file .env sentinel-ai-governance
```

### Serverless & Vercel
This repository is pre-configured with a `vercel.json` file, enabling zero-config deployments to Vercel via their container runtime. 
> [!WARNING]
> When deploying to serverless environments, you **must** connect to a managed PostgreSQL provider (e.g., AWS RDS, Supabase, Neon). Local SQLite fallback is not supported in production.

---

## 🧪 Quality Assurance & Testing

Sentinel maintains strict quality controls. Execute the comprehensive Pytest suite to validate the core routing, database abstractions, and agent logic:

```bash
# Run unit and integration tests with verbosity
pytest tests/ -v
```

---

<div align="center">
<i>Engineered for enterprise scalability, uncompromising security, and fully compliant AI autonomy.</i>
</div>
