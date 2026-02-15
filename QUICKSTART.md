# QUICK REFERENCE GUIDE

## Getting Started

### 1. Setup
```bash
# Clone & navigate
cd /Users/kalyani/Desktop/Projects/neuro-triage

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Install dependencies
pip install -r requirements.txt

# Start Docker services
docker-compose up -d
```

### 2. Initialize System
```bash
# Option A: Interactive (recommended)
python scripts/init_system.py

# Option B: Manual steps
python -m src.infrastructure.etl_patients           # Load synthetic patients
python -m src.infrastructure.ingest_docs           # Load medical knowledge
```

### 3. Run Services
```bash
# Terminal 1: Backend API
python -m src.api.main

# Terminal 2: Frontend UI
streamlit run src/ui/app.py

# Terminal 3: Optional - Evaluation
python scripts/evaluate_agent.py
```

### 4. Access
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Architecture Overview

```
[User Input (Streamlit UI)]
          ↓
[FastAPI Backend]
          ↓
[PARM Agent (LangGraph)]
  ├─ Planner (Triage)
  ├─ Actor (Retrieval & Generation)
  ├─ Critic (Safety Evaluation)
  ├─ Memory (Storage)
  └─ Feedback Loop (if score < 4)
          ↓
[Databases]
  ├─ PostgreSQL (Patient Data)
  ├─ Qdrant (Medical Knowledge)
  └─ Redis (Sessions)
          ↓
[Response to User]
```

---

## Key Concepts

### Triage Levels
- **Emergency** (Red): Immediate 911/ER required
  - Examples: chest pain, stroke, severe bleeding
  - Response: Hard-coded safety alert
  - Critic: Skipped

- **Urgent** (Yellow): Same-day evaluation needed
  - Examples: high fever, severe abdominal pain
  - Response: Recommend urgent care/ER
  - Critic: Applies standard checks

- **Routine** (Green): Schedule appointment
  - Examples: mild headache, general questions
  - Response: Evidence-based guidance
  - Critic: Full evaluation

### Safety Score (1-5)
- **5**: Fully safe, evidence-based, no concerns
- **4**: Mostly safe, minor clarifications recommended
- **3**: Some concerns, needs review
- **2**: Significant safety issues
- **1**: Dangerous, do not use

### Critic Node
The "Critic Agent" is System 2 thinking—it evaluates safety:
1. Checks retrieved docs align with claims
2. Verifies no contraindications exist
3. Ensures appropriate escalation
4. Scores response 1-5
5. If <4: suggests refinements

---

## Common Tasks

### Add a Patient
```python
from src.infrastructure.database import get_session
from src.memory.patient_manager import PatientManager

session = get_session()
manager = PatientManager(session)

patient_id = manager.create_patient({
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": datetime(1980, 5, 15).date(),
    "gender": "F",
    "email": "jane@example.com",
})

manager.add_medical_condition(
    patient_id=patient_id,
    condition_name="Hypertension",
    severity="moderate",
)
session.close()
```

### Test Agent Directly
```python
from src.agent import agent

result = agent.process_query(
    patient_id="test_001",
    user_input="I have severe chest pain and difficulty breathing",
)

print(f"Triage: {result['triage_level']}")
print(f"Response: {result['final_response']}")
print(f"Safety Score: {result['critique_score']}/5")
```

### Check API Health
```bash
curl http://localhost:8000/health
```

### Evaluate on Benchmarks
```bash
python scripts/evaluate_agent.py
# Outputs: evaluation_report_YYYYMMDD_HHMMSS.json
```

---

## Environment Variables (.env)

```
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults shown)
OPENAI_MODEL=gpt-4-turbo
DB_HOST=localhost
DB_PORT=5432
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
SAFETY_SCORE_MIN=4
```

---

## Troubleshooting

### "Connection refused" for PostgreSQL
- Check: `docker-compose ps`
- Ensure: `docker-compose up -d` completed
- Wait: Services take ~30s to start

### "OPENAI_API_KEY not found"
- Create `.env` file from `.env.example`
- Add your OpenAI API key
- Restart backend

### Qdrant search returns empty
- Run: `python -m src.infrastructure.ingest_docs`
- Verify: Documents appear in retrieval

### High latency (>10s)
- Check: LLM API response time
- Try: Smaller max_tokens in settings
- Monitor: Reflection iterations (should be 0-1)

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_agent.py::TestTriageClassification -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Monitoring

### Langfuse Dashboard
- Access: http://localhost:3000
- Track: Latencies, errors, LLM usage
- Filter: By user, session, date range

### Logs
- Location: `logs/` directory
- Files:
  - `neuro_triage.log`: Main application
  - `src.agent.log`: Agent-specific logs
  - `src.api.log`: API request logs

### Metrics
- Evaluation: `python scripts/evaluate_agent.py`
- Output: `evaluation_report_*.json`

---

## Deployment (Production)

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] No hardcoded API keys
- [ ] HTTPS enabled for API
- [ ] Database encrypted
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] HIPAA compliance review

### Docker Deployment
```bash
# Build image
docker build -t neuro-triage:latest .

# Run
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... neuro-triage:latest
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuro-triage
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: neuro-triage:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: secrets
              key: openai-key
```

---

## Research Paper Outline

### Title
**Neuro-Triage: A Reflective, Multi-Agent Clinical Decision Support System Using PARM Framework and Dual-Loop Verification**

### Sections
1. **Introduction** (1000 words)
   - Problem: Hallucination, amnesia, lack of metacognition in clinical LLMs
   - Gap: Limited agentic reasoning in healthcare
   - Contribution: PARM framework + Critic agent

2. **Related Work** (800 words)
   - RAG systems (Gao et al. 2023)
   - Agentic AI (Liu et al. 2024)
   - Clinical LLMs (Singhal et al. 2023)

3. **Methodology** (1500 words)
   - Architecture: LangGraph implementation
   - Safety mechanisms
   - Evaluation methodology

4. **Evaluation** (1200 words)
   - Dataset: MedQA + custom safety cases
   - Metrics: Recall, precision, latency
   - Results: Tables & figures

5. **Discussion** (800 words)
   - Findings, limitations, future work

6. **Conclusion** (400 words)

---

## Support

- **Documentation**: See README.md
- **Issues**: GitHub issues tab
- **Email**: your-email@example.com
- **Paper**: research/paper_draft.md

---

**Last Updated**: February 15, 2026  
**Version**: 0.1.0
