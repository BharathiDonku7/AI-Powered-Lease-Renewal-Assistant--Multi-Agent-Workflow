# Multi-Agent Lease Renewal Assistant

An agentic AI system that automates the lease renewal workflow end-to-end — from unstructured PDF documents to personalized resident communications — with built-in compliance guardrails and human-in-the-loop review.

Built as a focused slice of RealPage's Lumina AI Workforce architecture: a coordinated network of specialized AI agents that share context, take initiative, and route consequential decisions to humans.

## Why this matters

Property managers handle thousands of lease renewals every cycle. Done manually, it takes weeks. Done with a single autonomous LLM, it's unsafe — especially in regulated industries like property management where fair housing law and recent DOJ scrutiny make compliance non-negotiable. This system automates the routine cases and routes only the exceptions to humans, with a Compliance Agent that has veto power over every other agent.

## Architecture

```
PDF Lease / Rental Application
            ↓
    Document Ingestion Agent
            ↓
    Resident Profile Agent
            ↓
    Renewal Decision Agent  ←→  Market Lookup Tool
            ↓
    Compliance Agent (RAG over Fair Housing Rules)
            ↓
    ┌───────┼────────┐
    ↓       ↓        ↓
Approved Escalate  Vetoed
    ↓       ↓        ↓
Communication  Human Review  Blocked
   Agent         Queue
    ↓
Drafted Email
```

The workflow is implemented as a multi-agent system orchestrated with LangChain. Each agent has a focused responsibility, allowing the system to scale and remain auditable.

## Agents

- **Document Ingestion Agent** — accepts unstructured PDFs (rental applications, leases), extracts text with `pypdf`, and uses an LLM to convert it into structured resident data. Low-confidence extractions route to human review.
- **Resident Profile Agent** — converts raw resident data into a structured profile with tenure category, payment reliability, and risk signals. Never infers protected characteristics.
- **Renewal Decision Agent** — recommends a renewal strategy (standard renewal, retention discount, premium offer, do-not-renew). Has access to two tools it can invoke at runtime: a market intelligence lookup and a live external API for geographic context.
- **Compliance Agent** — performs RAG over a fair housing policy knowledge base (FAISS + HuggingFace embeddings) and has three possible verdicts: approved, escalate to human, or vetoed. Has veto authority over the entire pipeline.
- **Communication Agent** — drafts a personalized renewal email or text in the resident's preferred channel, with tone matched to the renewal type.

## Tech stack

- **LangChain** — agent orchestration, prompt management, and tool binding
- **Groq + Llama 3.3 70B** — fast, low-cost, open-source frontier inference
- **FAISS** — vector database for the Compliance Agent's RAG layer
- **HuggingFace Embeddings** (`sentence-transformers/all-MiniLM-L6-v2`) — local embedding model
- **Pydantic** — structured outputs and validation at every agent
- **pypdf** — PDF text extraction
- **Streamlit** — demo UI with file upload, agent reasoning trace, and human-review queue
- **Docker** — containerized deployment

## What it demonstrates

- Multi-agent orchestration with five specialized agents
- Multi-step reasoning across the agent pipeline
- Tool-calling — the Decision Agent dynamically invokes a market data tool and a live external API
- RAG architecture with vector embeddings
- Structured outputs with Pydantic at every step
- Guardrails — compliance veto, confidence thresholds, human escalation
- Production thinking — audit trail, exception handling, regulated-industry safety patterns
- Containerized deployment ready for cloud platforms

## Project structure

```
lease-renewal-agents/
├── agents/
│   ├── document_ingestion_agent.py
│   ├── resident_profile_agent.py
│   ├── renewal_decision_agent.py
│   ├── compliance_agent.py
│   └── communication_agent.py
├── tools/
│   └── market_tools.py
├── data/
│   └── residents.json
├── knowledge_base/
│   └── fair_housing_rules.txt
├── sample_documents/
│   └── rental_application_sample.pdf
├── orchestrator.py
├── main.py
├── app.py
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=your_groq_key" > .env
```

Get a free Groq API key at https://console.groq.com/keys

## Run

CLI — runs the pipeline against all sample residents:

```bash
python main.py
```

Streamlit UI — upload a PDF or pick a sample resident:

```bash
streamlit run app.py
```

Open http://localhost:8501

## Run with Docker

```bash
docker build -t lease-renewal-agents .
docker run -p 8501:8501 --env-file .env lease-renewal-agents
```

Open http://localhost:8501

## How it maps to RealPage

- Mirrors **Lumina AI Workforce's** architecture — coordinated specialized agents that share context
- Directly addresses **unstructured document workflows with exception handling and human review**
- The Compliance Agent + human-review queue address the **post-DOJ settlement need** for transparency, auditability, and human oversight in AI decisions
- Designed to scale renewal processing **10–100x** by automating routine cases and routing only exceptions to humans

## Author

Bharathi Donku — AI/ML Engineer
