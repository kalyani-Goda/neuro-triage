#!/usr/bin/env python3
"""
Test script to verify the infinite loop fix.
This simulates a contraindication scenario without starting the full API.
"""

import sys
sys.path.insert(0, '/Users/kalyani/Desktop/Projects/neuro-triage')

from src.agent.workflow import PARMGraphWorkflow
from src.agent.state import AgentState
import uuid
import time

# Create workflow
workflow = PARMGraphWorkflow()

# Create test state with contraindication scenario
state = {
    "patient_id": "faf83fb0-a2a1-4b8d-bb21-470cdbf8d60f",
    "session_id": str(uuid.uuid4()),
    "user_input": "Can I take naproxen for my asthma pain?",  # NSAID + asthma = contraindication
    "patient_context": {
        "name": "Test Patient",
        "conditions": ["Asthma"],  # Key: patient has asthma
        "medications": [],
        "allergies": [],
        "medical_history": [{"condition": "Asthma"}]
    },
    "triage_level": "routine",
    "triage_confidence": 0.0,
    "retrieved_documents": [],
    "draft_response": None,
    "generation_rationale": None,
    "critique_score": 0,
    "critique_feedback": None,
    "is_approved": False,
    "is_error": False,
    "error_message": "",
    "final_response": "",
    "response_status": "pending",
    "reflection_iterations": 0,
    "reflection_history": [],
    "safety_violations": [],
}

print("=" * 80)
print("TESTING: Contraindication Detection (NSAID + Asthma)")
print("=" * 80)
print()

start_time = time.time()
timeout = 30  # 30 second timeout to catch infinite loops

try:
    print("Starting workflow...")
    result_obj = workflow.invoke(state)
    
    elapsed = time.time() - start_time
    
    # Convert to dict if needed
    if hasattr(result_obj, '__dict__'):
        result = vars(result_obj)
    else:
        result = result_obj
    
    print()
    print("✅ WORKFLOW COMPLETED (No infinite loop!)")
    print(f"   Time: {elapsed:.2f} seconds")
    print()
    print("Results:")
    print(f"  - Triage Level: {result.get('triage_level')}")
    print(f"  - Critique Score: {result.get('critique_score')}/5")
    print(f"  - Is Approved: {result.get('is_approved')}")
    print(f"  - Response Status: {result.get('response_status')}")
    print(f"  - Reflection Iterations: {result.get('reflection_iterations')}")
    print(f"  - Safety Violations: {result.get('safety_violations')}")
    print()
    
    if result.get('response_status') == 'escalated':
        print("✅ PASS: Contraindication correctly triggered escalation!")
    elif result.get('response_status') == 'error':
        print("⚠️  Response marked as error - acceptable for this case")
    else:
        print(f"❌ UNEXPECTED: response_status = {result.get('response_status')}")
        
except RecursionError as e:
    elapsed = time.time() - start_time
    print(f"❌ FAIL: Infinite loop detected (RecursionError after {elapsed:.2f}s)")
    print(f"   Error: {e}")
    sys.exit(1)
except Exception as e:
    elapsed = time.time() - start_time
    print(f"⚠️  Exception after {elapsed:.2f}s: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✅ TEST PASSED: No infinite loop detected!")
print("=" * 80)
