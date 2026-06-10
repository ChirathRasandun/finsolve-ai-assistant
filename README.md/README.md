# 🏦 FinSolve AI Assistant
### RAG-Based Chatbot with Role-Based Access Control (RBAC)

> Built by Chirath Rasandun· June 2026

---

## What is this?

FinSolve AI Assistant is an internal enterprise chatbot that lets employees query private company data using natural language. It uses **RAG (Retrieval Augmented Generation)** to ground answers in real documents, and **RBAC** to ensure each user only sees data their role permits.

---

## Features

- ✅ **RAG Pipeline** — answers from real company documents via ChromaDB
- ✅ **RBAC** — 6 role levels with strict document-level filtering
- ✅ **Guardrails** — PII protection + out-of-scope detection
- ✅ **Monitoring** — token cost tracking, query logs, violation alerts
- ✅ **JWT Auth** — secure login with 83 employee accounts from HR CSV
- ✅ **Professional UI** — dark themed Streamlit chat interface

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python |
| LLM | OpenAI GPT-3.5 Turbo |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector Store | ChromaDB |
| RAG Framework | LangChain |
| Authentication | JWT (python-jose) |
| Frontend | Streamlit |

---

## Project Structure

```
rag-rbac-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── auth.py           # JWT auth + user loading from CSV
│   │   ├── rag_engine.py     # RAG pipeline
│   │   ├── rbac.py           # Role-based document filtering
│   │   ├── data_loader.py    # Document loader
│   │   ├── guardrails.py     # Safety layer
│   │   ├── monitoring.py     # Token + query logging
│   │   └── models.py         # Pydantic models
│   ├── data/
│   │   ├── finance/          # Finance role only
│   │   ├── marketing/        # Marketing role only
│   │   ├── hr/               # HR role only
│   │   ├── engineering/      # Engineering role only
│   │   └── general/          # All employees
│   └── requirements.txt
├── frontend/
│   └── streamlit_app.py
└── .env
```

---

## Setup

### 1. Configure environment
```bash
# Create .env file
OPENAI_API_KEY=your_key_here
SECRET_KEY=your_secret_here
```

### 2. Install dependencies
```bash
cd backend
pip install fastapi uvicorn langchain langchain-community langchain-openai
pip install langchain-huggingface langchain-chroma chromadb
pip install sentence-transformers openai pandas pypdf python-dotenv
pip install python-jose passlib tenacity pydantic streamlit requests
```

### 3. Start backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Start frontend
```bash
cd frontend
streamlit run streamlit_app.py
```

Open: http://localhost:8501

---

## Roles & Access

| Role | Department | Access |
|---|---|---|
| 💰 Finance | Finance | Financial reports, budgets |
| 📈 Marketing | Marketing | Campaigns, ROI, customer data |
| 👥 HR | HR | Employee records, payroll |
| ⚙️ Engineering | Technology / QA / Data | Architecture, tech stack |
| 👑 Executive | C-Level | Full access to everything |
| 🧑‍💼 Employee | All others | General policies, FAQs |

**All demo passwords:** `password123`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /login | Authenticate, returns JWT |
| POST | /query | RAG query with RBAC |
| GET | /health | System health + cost stats |
| GET | /docs | Swagger UI |

---

## RBAC Test Cases

| Role | ✅ Can Ask | ❌ Cannot Ask |
|---|---|---|
| Finance | Q4 revenue? | Employee salaries? |
| Marketing | Marketing ROI? | Gross profit? |
| HR | Performance ratings? | Q4 revenue? |
| Engineering | System architecture? | Payroll details? |
| Executive | Anything | Nothing blocked |
| Employee | Leave policy? | Anyone's salary? |

---

## Monitoring

- Query logs → `backend/query_logs.json`
- Violation logs → `backend/violations_log.json`
- Health check → `http://localhost:8000/health`
