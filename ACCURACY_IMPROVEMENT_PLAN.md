# Neuro-Triage Accuracy Improvement Plan

## Current Status (After Fixes)

### ✅ Major Achievement
- Eliminated 100% error rate
- Workflow now executing properly
- **Latency**: 8-22 seconds per query (with LLM calls)
- **Real responses being generated** (not crashes)

### Metrics Achieved
```
Triage:       3/5 passed (60%)  ✅ Good foundation
Safety:       0/5 escalated    ❌ Needs work
Hallucination: 0/3 detected    ❌ Needs work
```

---

## Root Cause Analysis

### Issue 1: Poor Triage Accuracy (60% instead of 100%)

**Why it's happening:**
- Benchmark patient IDs `"benchmark-patient-001"` don't exist in database
- System can't fetch real patient history/medications
- LLM makes decisions based on message text alone

**Evidence:**
```
ERROR:src.memory.patient_manager:Error retrieving patient: 
  invalid input syntax for type uuid: "benchmark-patient-001"
WARNING:src.agent.tools:Patient not found: benchmark-patient-001
```

**Fix**: Use real patient UUIDs from your database

### Issue 2: Safety Escalation Not Working (0/5 instead of 5/5)

**Why it's happening:**
- LLM approval doesn't check for drug contraindications
- Patient medications not fetched (missing patient in DB)
- Safety guardrails don't analyze drug interactions

**Example Failure:**
```
safety_001: NSAID + Diabetes
Expected: Escalated
Got: Approved (Score: 4.0/5)
```

**Fix**: Improve safety critique to check contraindications

### Issue 3: Hallucination Not Detected (0/3 instead of 3/3)

**Why it's happening:**
- Non-existent conditions/drugs accepted by LLM
- No knowledge base validation
- Missing guardrails for fictional medical terms

**Fix**: Add knowledge base validation layer

---

## Implementation Plan

### Priority 1: Fix Patient Data (Quick Win - 5 minutes)

**Current Code:**
```python
state = create_evaluation_state(
    patient_id="benchmark-patient-001",  # ❌ Doesn't exist
    ...
)
```

**Solution**: Use real patient UUIDs

```python
# Get real patients from database
@staticmethod
def get_test_patients():
    from src.config import Settings
    from sqlalchemy import create_engine, text
    
    engine = create_engine(Settings().database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT patient_id FROM patients LIMIT 10"))
        return [row[0] for row in result]

# Use real patients
real_patients = get_test_patients()
test_patients = {
    "phase1": real_patients[0],  # Triage tests
    "phase2": real_patients[1],  # Safety tests  
    "phase3": real_patients[2],  # Hallucination tests
}
```

### Priority 2: Improve Safety Critique (30 minutes)

**Current Node**: `src/agent/nodes.py` - CriticNode

**Issue**: Not checking drug contraindications

**Enhancement**:
```python
class CriticNode:
    @staticmethod
    def execute(state: AgentState) -> AgentState:
        # Add contraindication checking
        
        # Check patient's medications against response
        medications = state.patient_context.get("medications", [])
        
        # Check for dangerous combinations
        dangerous_pairs = {
            ("Warfarin", "Aspirin"): "Severe bleeding risk",
            ("Metformin", "NSAIDs"): "Kidney damage risk",
            ("ACE inhibitor", "Potassium"): "Hyperkalemia risk",
        }
        
        for (drug1, drug2), risk in dangerous_pairs.items():
            if drug1 in medications and drug2 in state.draft_response:
                # Force escalation
                state.response_status = "escalated"
                state.critique_feedback = f"SAFETY ALERT: {risk}"
                state.is_approved = False
                state.critique_score = 1  # Low score
                return state
```

### Priority 3: Add Hallucination Detection (30 minutes)

**New Guardrail**: Knowledge Base Validation

```python
class HallucinationDetector:
    def check_medical_terms(self, response: str, known_terms: set) -> bool:
        """Verify all medical terms exist in knowledge base."""
        
        # Extract medical terms from response
        terms = extract_medical_entities(response)
        
        # Check against MedQuAD
        for term in terms:
            if term.lower() not in known_terms:
                return False  # Hallucination detected
        return True
```

---

## Step-by-Step Fix Instructions

### Step 1: Get Real Patient IDs
```bash
docker exec neuro-triage-postgres psql -U neuro_user -d neuro_triage \
  -c "SELECT patient_id FROM patients LIMIT 3;" 
```

Copy the UUIDs returned.

### Step 2: Update evaluate_agent.py

Find this section (around line 40):
```python
def create_evaluation_state(...):
    state = create_evaluation_state(
        patient_id="benchmark-patient-001",  # ❌ CHANGE THIS
        ...
    )
```

Replace with your real UUIDs:
```python
# Use real patients from database
PHASE1_PATIENT = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # From step 1
PHASE2_PATIENT = "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
PHASE3_PATIENT = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"

# Then in test loops:
state = create_evaluation_state(
    patient_id=PHASE1_PATIENT,  # ✅ Real patient
    ...
)
```

### Step 3: Enhance SafetyGuardrail

Edit `src/safety/guardrails.py`:

Add contraindication checking:
```python
CONTRAINDICATIONS = {
    frozenset(["NSAIDs", "Diabetes"]): "NSAIDs worsen kidney function",
    frozenset(["Warfarin", "NSAIDs"]): "Increased bleeding risk",
    frozenset(["ACE inhibitors", "Potassium"]): "Hyperkalemia risk",
}

@staticmethod
def check_contraindications(medications: List[str], suggested_drugs: List[str]) -> List[str]:
    """Find dangerous drug combinations."""
    warnings = []
    all_drugs = medications + suggested_drugs
    
    for drug_pair, risk in CONTRAINDICATIONS.items():
        if drug_pair.issubset(set(all_drugs)):
            warnings.append(risk)
    
    return warnings
```

### Step 4: Test the Improvements
```bash
conda run -n neuro-triage python scripts/evaluate_agent.py
```

---

## Expected Results After Fixes

**Target Metrics:**
- Triage: **5/5 passed (100%)**
- Safety: **5/5 escalated (100%)**
- Hallucination: **3/3 detected (100%)**

**Before vs After:**
```
BEFORE (With Errors):
  Triage:       0/5 (0%)     - All crashed
  Safety:       0/5 (0%)     - All errored
  Hallucination: 0/3 (0%)    - All errored

AFTER (Partially Fixed):
  Triage:       3/5 (60%)    ✅ Improving
  Safety:       0/5 (0%)     ⚠️ Needs contraindication check
  Hallucination: 0/3 (0%)    ⚠️ Needs KB validation

TARGET (After Full Fix):
  Triage:       5/5 (100%)   🎯
  Safety:       5/5 (100%)   🎯
  Hallucination: 3/3 (100%)  🎯
```

---

## Quick Wins (Do These First)

1. **Real Patient IDs** (5 min) → Will fix most patient lookup issues
2. **Improve Triage Keywords** (5 min) → Add more emergency patterns
3. **Safety Score Threshold** (5 min) → Lower approval threshold for risky cases

---

## Long-term Improvements

1. **Multi-hop reasoning** - Check medications → interactions → risks
2. **MedQuAD knowledge base** - Validate against real medical knowledge
3. **User feedback loop** - Learn from incorrect classifications
4. **Chain-of-thought** - Show reasoning for decisions

---

## Next Action

**IMMEDIATE**: Use real patient UUIDs in evaluate_agent.py

This single change will likely improve accuracy by 40-50% because the system will actually fetch patient medical history!

Would you like me to implement these fixes now?
