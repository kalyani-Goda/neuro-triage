# NEURO-TRIAGE: FILE REFERENCE GUIDE

## Quick Navigation

Find what you need by looking at these key files:

---

## 📋 **Documentation Files**

| File | Purpose | Read When |
|------|---------|-----------|
| [README.md](README.md) | Full project documentation | First thing - start here! |
| [QUICKSTART.md](QUICKSTART.md) | Quick reference & common tasks | Setting up or troubleshooting |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | High-level overview | Getting oriented |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture & roadmap | Understanding design |
| [FILE_GUIDE.md](FILE_GUIDE.md) | This file | Finding specific files |

---

## 🔧 **Configuration & Setup**

| File | Purpose | What You Do |
|------|---------|-----------|
| `.env.example` | Environment template | Copy to `.env` and fill in |
| `requirements.txt` | Python dependencies | Run `pip install -r requirements.txt` |
| `docker-compose.yml` | Container orchestration | Run `docker-compose up -d` |
| `docker/init_db.sql` | Database schema | Loaded automatically by Docker |

---

## 🤖 **Core Agent Files** (`src/agent/`)

| File | Class/Function | Purpose |
|------|---|---------|
| `__init__.py` | `NeuroTriageAgent` | Main agent interface - **USE THIS** |
| `state.py` | `AgentState` | Data structure for agent state |
| `nodes.py` | `PlannerNode`, `ActorNode`, `CriticNode`, `MemoryNode` | PARM framework nodes |
| `tools.py` | `RetrievalTool`, `LLMTool`, `EmbeddingManager` | LLM tools & utilities |
| `workflow.py` | `PARMGraphWorkflow` | LangGraph compilation |
| `enhancements.py` | Advanced features | Multi-factor scoring, explainability |

### How to Use Agent
```python
from src.agent import agent

result = agent.process_query(
    patient_id="patient_001",
    user_input="I have chest pain",
)
```

---

## 🛡️ **Safety & Compliance** (`src/safety/`)

| File | Class | Purpose |
|------|-------|---------|
| `guardrails.py` | `SafetyGuardrail`, `TriageLevel` | Emergency detection, contraindications |
| `pii_protection.py` | `PIIProtector` | PII masking with Presidio |

### When to Use
- `SafetyGuardrail`: Check if a response is safe
- `PIIProtector`: Mask sensitive data from input

---

## 💾 **Patient & Memory Management** (`src/memory/`)

| File | Class | Purpose |
|------|-------|---------|
| `models.py` | ORM Models | SQLAlchemy database tables |
| `patient_manager.py` | `PatientManager` | Patient CRUD operations |

### Common Operations
```python
from src.infrastructure.database import get_session
from src.memory.patient_manager import PatientManager

session = get_session()
manager = PatientManager(session)
patient = manager.get_patient("patient_id")
```

---

## 🗄️ **Infrastructure** (`src/infrastructure/`)

| File | Class | Purpose |
|------|-------|---------|
| `database.py` | SQLAlchemy setup | PostgreSQL connection |
| `qdrant_manager.py` | `QdrantManager` | Vector database operations |
| `redis_manager.py` | `RedisManager` | Cache & session management |
| `etl_patients.py` | `PatientETL` | Generate & load synthetic patients |
| `ingest_docs.py` | `MedicalKnowledgeIngester` | Load medical knowledge to Qdrant |

### Common Operations
```bash
# Load synthetic patients (100)
python -m src.infrastructure.etl_patients

# Load medical documents
python -m src.infrastructure.ingest_docs
```

---

## 📊 **Evaluation** (`src/evaluation/`)

| File | Class | Purpose |
|------|-------|---------|
| `metrics.py` | `EvaluationMetrics`, `BenchmarkEvaluator` | Compute evaluation metrics |
| `benchmarks.py` | Constants | Test datasets (MedQA, Safety cases) |

### Run Evaluation
```bash
python scripts/evaluate_agent.py
# Outputs: evaluation_report_YYYYMMDD_HHMMSS.json
```

---

## 🌐 **API Backend** (`src/api/`)

| File | Function | Endpoints |
|------|----------|-----------|
| `main.py` | FastAPI app | POST `/chat`, GET `/health`, POST `/initialize` |

### Test API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "test_001", "message": "I have chest pain"}'
```

---

## 🎨 **Frontend UI** (`src/ui/`)

| File | Framework | Purpose |
|------|-----------|---------|
| `app.py` | Streamlit | Web interface for clinical consultation |

### Start UI
```bash
streamlit run src/ui/app.py
# Open: http://localhost:8501
```

---

## 🧪 **Testing** (`tests/`)

| File | Test Class | What's Tested |
|------|-----------|---------------|
| `test_agent.py` | Multiple test classes | Triage, PII, guardrails, agent |

### Run Tests
```bash
pytest tests/ -v
pytest tests/test_agent.py::TestTriageClassification -v
```

---

## 🚀 **Scripts** (`scripts/`)

| Script | Purpose | Run With |
|--------|---------|----------|
| `init_system.py` | Initialize system | `python scripts/init_system.py` |
| `evaluate_agent.py` | Run benchmarks | `python scripts/evaluate_agent.py` |

---

## 🎯 **Utility Files** (`src/`)

| File | Purpose |
|------|---------|
| `config.py` | Configuration management |
| `logging_config.py` | Logging setup |
| `utils.py` | Helper functions |

---

## 📁 **Data Directories**

| Directory | Contains | Used For |
|-----------|----------|----------|
| `data/patients/` | Synthetic patient JSONs | Example data |
| `data/medical_knowledge/` | Knowledge documents | RAG source documents |
| `logs/` | Application logs | Debugging & monitoring |

---

## 🔑 **Key File Relationships**

```
user query
    ↓ (via Streamlit UI)
src/ui/app.py
    ↓ (HTTP POST)
src/api/main.py
    ↓ (calls)
src/agent/__init__.py (NeuroTriageAgent)
    ↓ (uses)
src/agent/workflow.py (LangGraph)
    ↓ (invokes)
    ├─ src/agent/nodes.py (Planner, Actor, Critic, Memory)
    ├─ src/safety/guardrails.py (Safety checks)
    ├─ src/safety/pii_protection.py (PII masking)
    ├─ src/agent/tools.py (Retrieval, LLM)
    └─ src/memory/patient_manager.py (Get patient context)
    ↓ (queries/stores data in)
    ├─ src/infrastructure/qdrant_manager.py (Medical knowledge)
    ├─ src/infrastructure/database.py (Patient data)
    └─ src/infrastructure/redis_manager.py (Session cache)
    ↓
Final response back to user
```

---

## 📝 **How to Modify**

### Add a New Safety Check
1. Edit: `src/safety/guardrails.py`
2. Add method to `SafetyGuardrail` class
3. Call in: `src/agent/nodes.py` in `CriticNode`

### Add a New Evaluation Metric
1. Edit: `src/evaluation/metrics.py`
2. Add method to `EvaluationMetrics` class
3. Use in: `scripts/evaluate_agent.py`

### Add a New API Endpoint
1. Edit: `src/api/main.py`
2. Add `@app.get()` or `@app.post()` function
3. Test via: `curl` or Swagger UI

### Add a New Database Field
1. Edit: `src/memory/models.py` (add to ORM model)
2. Update: `docker/init_db.sql` (schema)
3. Recreate database: `docker-compose down && docker-compose up -d`

---

## 🔍 **Finding Specific Functionality**

### "I want to..."

**Check if patient has allergy**
→ See: `src/memory/patient_manager.py` → `get_patient()`

**Add a new medication interaction**
→ See: `src/safety/guardrails.py` → `CONTRAINDICATIONS`

**Evaluate agent on my own dataset**
→ See: `src/evaluation/metrics.py` → `BenchmarkEvaluator`

**Modify the triage algorithm**
→ See: `src/agent/nodes.py` → `PlannerNode.execute()`

**Change API response format**
→ See: `src/api/main.py` → `TriageResponse` model

**Add new patient to database**
→ See: `src/memory/patient_manager.py` → `create_patient()`

**Query medical knowledge base**
→ See: `src/infrastructure/qdrant_manager.py` → `search()`

**Change critique scoring**
→ See: `src/agent/nodes.py` → `CriticNode.execute()`

**Add UI feature**
→ See: `src/ui/app.py` → Add Streamlit component

---

## 📚 **File Statistics**

```
Total Files: 35
├── Python Code: 28 files (~3,500 lines)
├── Documentation: 5 files (~1,500 lines)
├── Configuration: 2 files
└── Schema: 1 file

By Module:
├── Agent: 6 files (1,200 lines)
├── Safety: 2 files (300 lines)
├── Memory: 2 files (250 lines)
├── Infrastructure: 5 files (800 lines)
├── Evaluation: 2 files (400 lines)
├── API: 1 file (200 lines)
├── UI: 1 file (300 lines)
├── Tests: 1 file (200 lines)
└── Core: 3 files (200 lines)
```

---

## 🔄 **Workflow: From Feature Request to Implementation**

1. **Design**: Add to `ARCHITECTURE.md` roadmap
2. **Implement**: Choose file from this guide
3. **Test**: Add to `tests/test_agent.py`
4. **Document**: Update docstrings + README
5. **Evaluate**: Run `scripts/evaluate_agent.py`

---

## 🆘 **Need Help?**

| Question | File | Section |
|----------|------|---------|
| How do I start? | README.md | Quick Start |
| Where's the API docs? | src/api/main.py | FastAPI auto-docs |
| How does safety work? | src/safety/ | All files |
| How do I add a patient? | src/memory/patient_manager.py | `create_patient()` |
| How do I run tests? | tests/test_agent.py | Run with pytest |
| What's the evaluation? | src/evaluation/metrics.py | All methods |
| How's the database set up? | docker/init_db.sql | SQL schema |
| How do I extend the agent? | src/agent/nodes.py | Add custom node |

---

## ✨ **Pro Tips**

1. **Start with**: README.md → QUICKSTART.md → specific files
2. **Use Ctrl+F (search)** to find patterns across files
3. **Follow imports** - they show dependencies
4. **Check docstrings** - comprehensive documentation in code
5. **Run tests first** - verify setup is correct
6. **Monitor logs** - `tail -f logs/neuro_triage.log`
7. **Use Git** - track all changes

---

**Last Updated**: February 15, 2026  
**Version**: v0.1.0

Good luck exploring! 🚀
