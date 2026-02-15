# Neuro-Triage: A Reflective, Multi-Agent Clinical Decision Support System

## 📋 Overview

**Neuro-Triage** is a research-grade clinical decision support system implementing the **PARM Framework** (Planning, Action, Reflection, Memory) using **LangGraph** for agentic reasoning. Unlike standard RAG systems, Neuro-Triage employs **System 2 Thinking** via a Critic Agent to perform dual-loop verification of clinical responses, ensuring safety and reducing hallucinations.

### Key Innovation: Reflective Critique
The system uses a **Critic Agent** (System 2) that evaluates every clinical response against safety thresholds before presenting it to users. If safety concerns are detected, the response is refined or escalated.

---

## 🎯 Research Objectives

### Primary Hypothesis
Integrating a Reflective Critic Node (System 2) into a clinical agent workflow reduces hazardous hallucinations by **>40%** compared to zero-shot RAG baseline, while maintaining **>98% Triage Recall** for emergency cases.

### Metrics
1. **Hallucination Rate** (Ragas Faithfulness)
2. **Triage Recall** (Emergency case detection)
3. **Latency Analysis** (Cost of \"thinking\")
4. **Safety Score Distribution** (1-5 scale)

---

## 🏗️ Architecture

### PARM Framework Components

```
User Input
    ↓
[1] PLANNER (Triage) → Classify urgency (Emergency/Urgent/Routine)
    ↓
[2] ACTOR (Retrieval & Generation) → Retrieve context + Generate draft
    ↓
[3] CRITIC (Reflection) → Evaluate safety, Score 1-5
    ↓
    Is Score ≥ 4?
    ├─ YES → [4] MEMORY → Store & Return
    └─ NO → Refine (loop back to ACTOR, max 3 iterations)
    ↓
Final Safe Response
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | LangGraph |
| **LLM** | OpenAI GPT-4 Turbo |
| **Vector DB** | Qdrant (Medical Knowledge) |
| **SQL DB** | PostgreSQL (Patient Records) |
| **Caching** | Redis (Session State) |
| **Observability** | Langfuse |
| **API** | FastAPI |
| **Frontend** | Streamlit |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- OpenAI API Key
- 8GB RAM, 20GB disk

### Installation

1. **Clone and setup**:
```bash
cd /Users/kalyani/Desktop/Projects/neuro-triage
cp .env.example .env
# Edit .env with your OpenAI API key
```

2. **Start infrastructure**:
```bash
docker-compose up -d
# Wait for all services to be healthy (~30s)
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Initialize system**:
```bash
python -m src.infrastructure.etl_patients  # Load 100 synthetic patients
python -m src.infrastructure.ingest_docs   # Load medical knowledge
```

5. **Start backend**:
```bash
python -m src.api.main
# API runs on http://localhost:8000
```

6. **Start frontend** (in another terminal):
```bash
streamlit run src/ui/app.py
# UI runs on http://localhost:8501
```

---

## 📊 Project Structure

```
neuro-triage/
├── src/
│   ├── agent/                    # LangGraph PARM workflow
│   │   ├── state.py              # AgentState dataclass
│   │   ├── nodes.py              # Planner, Actor, Critic, Memory nodes
│   │   ├── tools.py              # LLM tools (retrieval, embeddings)
│   │   ├── workflow.py           # LangGraph compilation
│   │   └── __init__.py           # Main NeuroTriageAgent
│   ├── safety/                   # Safety & compliance
│   │   ├── guardrails.py         # Triage, contraindication checks
│   │   └── pii_protection.py     # Presidio-based PII masking
│   ├── memory/                   # Patient data management
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── patient_manager.py    # Patient CRUD operations
│   ├── infrastructure/           # Database & external services
│   │   ├── database.py           # PostgreSQL setup
│   │   ├── qdrant_manager.py     # Vector DB operations
│   │   ├── redis_manager.py      # Session caching
│   │   ├── etl_patients.py       # Synthetic data generation
│   │   └── ingest_docs.py        # Medical knowledge ingestion
│   ├── evaluation/               # Metrics & benchmarking
│   │   ├── metrics.py            # Evaluation metrics (Ragas, recall)
│   │   └── benchmarks.py         # Test case datasets
│   ├── api/                      # FastAPI backend
│   │   └── main.py               # REST API endpoints
│   ├── ui/                       # Streamlit frontend
│   │   └── app.py                # Web UI
│   └── config.py                 # Configuration management
├── tests/
│   └── test_agent.py             # Unit & integration tests
├── docker/
│   └── init_db.sql               # PostgreSQL schema
├── data/
│   ├── patients/                 # Synthetic patient JSONs
│   └── medical_knowledge/        # Knowledge base documents
├── docs/                         # Research documentation
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Multi-container setup
└── .env.example                  # Configuration template
```

---

## 🔄 Workflow Example

**Input**: \"Patient reports sudden chest pain and shortness of breath\"

### Step 1: Planning (Triage)
- **Input**: Raw symptom description
- **Output**: `triage_level = "emergency"`, confidence = 0.95
- **Action**: Trigger emergency protocol

### Step 2: Action (Retrieval & Generation)
- **Skipped** for emergency: Returns hard-coded emergency response
- **For non-emergency**: Retrieves guidelines from Qdrant
- **Output**: Draft response

### Step 3: Reflection (Critique)
- **Evaluation Criteria**:
  - Evidence-based (uses retrieved context)?
  - No dangerous language patterns?
  - Respects patient allergies/contraindications?
  - Appropriate triage level?
- **Output**: Safety score = 5/5 ✓ Approved
- **If score < 4**: Loop back to Action with refined prompt

### Step 4: Memory
- Store session in Redis + PostgreSQL
- Log conversation for audit

### Final Output
```json
{
  "final_response": "🚨 EMERGENCY ALERT...\nCALL 911 IMMEDIATELY",
  "triage_level": "emergency",
  "critique_score": 5,
  "response_status": "approved",
  "reflection_iterations": 0
}
```

---

## 📈 Evaluation Methodology

### Dataset
- **Triage**: Custom + MedQA subset (50 questions)
- **Safety**: Adversarial test cases (10 contraindication scenarios)
- **Hallucination**: Non-existent condition queries

### Metrics Calculated

**1. Hallucination Rate** (Lower is better)
```
= False claims / Total responses
Target: < 30% (vs. 50-70% for zero-shot LLM)
```

**2. Triage Recall** (Higher is better)
```
= Emergency cases correctly identified / All true emergencies
Target: > 98%
```

**3. Latency** (Lower is better)
```
- Reflection overhead (added by Critic node)
- p95 latency: target < 5 seconds
```

### Running Evaluation
```bash
python scripts/evaluate_agent.py
# Output: metrics_report_<timestamp>.json
```

---

## 🛡️ Safety Features

### 1. Deterministic Emergency Handling
- Hard-coded response for emergency cases
- Bypasses LLM for critical situations
- 100% recall guaranteed for emergency keywords

### 2. PII Protection
- Detects & masks: SSN, credit cards, names, emails, phone numbers
- Uses Microsoft Presidio
- Prevents data leakage to LLM

### 3. Contraindication Checking
- Drug-condition interactions (e.g., NSAID + kidney disease)
- Drug-drug interactions (e.g., duplicate NSAID classes)
- Respects patient allergies

### 4. Dual-Loop Verification
- Draft response automatically scored (1-5)
- Unsafe responses rejected or refined
- Max 3 refinement iterations to prevent infinite loops

### 5. Audit Logging
- All queries logged with timestamps
- PII stripped from logs
- Compliance-ready for HIPAA requirements

---

## 🔧 Configuration

Edit `.env` file:

```env
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Databases
DB_USER=neuro_user
DB_PASSWORD=secure_password
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0

# Safety Thresholds
SAFETY_SCORE_MIN=4
HALLUCINATION_THRESHOLD=0.3
TRIAGE_RECALL_TARGET=0.98

# Observability
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
```

---

## 📚 API Documentation

### POST /chat
Process a patient query through the PARM workflow.

**Request**:
```json
{
  "patient_id": "patient_001",
  "message": "I have severe chest pain",
  "session_id": "optional-uuid"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "patient_id": "patient_001",
  "final_response": "🚨 EMERGENCY ALERT...",
  "triage_level": "emergency",
  "triage_confidence": 0.95,
  "critique_score": 5,
  "response_status": "approved",
  "reflection_iterations": 0,
  "success": true
}
```

### GET /health
Check system health (database, vector DB, cache, API).

### POST /initialize
Initialize databases, Qdrant collection, load synthetic data.

---

## 🧪 Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_agent.py::TestTriageClassification::test_emergency_detection -v
```

---

## 📖 Research Paper Structure

The project validates the following claims:

1. **Novelty**: PARM framework computationally realized in LangGraph
2. **Safety**: Dual-loop verification reduces unsafe responses
3. **Realism**: Hybrid memory (SQL + Vector), FHIR-compatible patient data
4. **Evaluation**: Rigorous metrics (Ragas, Recall, Latency)

**Expected paper outline**:
1. Introduction: The \"Amnesia\" and \"Hallucination\" problem in clinical LLMs
2. Related Work: System 1 vs. System 2, Agentic RAG
3. Methodology: PARM framework, LangGraph architecture
4. Evaluation: Metrics, datasets, results
5. Discussion: Limitations, future work, deployment considerations
6. Conclusion: Clinical LLMs need reflective reasoning

---

## 🚨 Limitations & Future Work

### Current Limitations
- Critic agent still LLM-based (not 100% deterministic)
- Limited medical knowledge base (sample data)
- No user authentication/HIPAA encryption
- Single LLM provider (OpenAI)

### Enhancements for v1.0
- Multi-LLM support (Claude, Llama, etc.)
- Domain-specific critic rules (hard-coded med rules)
- End-to-end encryption
- Real EHR system integration
- Advanced hallucination detection (entity consistency)
- Federated learning for continuous improvement

---

## 📝 Citation

If you use Neuro-Triage in research, cite as:

```bibtex
@software{neuro_triage_2026,
  title={Neuro-Triage: A Reflective, Multi-Agent Clinical Decision Support System},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/neuro-triage}
}
```

---

## 📞 Support & Questions

- **Issues**: Create GitHub issue
- **Discussions**: GitHub discussions
- **Email**: your-email@example.com

---

## ⚠️ Disclaimer

**Neuro-Triage is a RESEARCH PROTOTYPE, not for clinical use without proper validation and regulatory approval.** This system should never replace professional medical judgment. All responses should be reviewed by qualified healthcare providers before acting upon them.

---

## 📄 License

MIT License - See LICENSE file

---

**Last Updated**: February 15, 2026  
**Status**: Active Development (v0.1.0)
