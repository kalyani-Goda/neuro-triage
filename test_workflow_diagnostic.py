#!/usr/bin/env python3
"""Diagnostic script to identify workflow issues."""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.workflow import PARMGraphWorkflow
from src.agent.nodes import TriageLevel
import logging

logging.basicConfig(level=logging.DEBUG)

print("="*70)
print("WORKFLOW DIAGNOSTIC TEST")
print("="*70)

# Test 1: Workflow initialization
print("\n[TEST 1] Workflow Initialization")
try:
    workflow = PARMGraphWorkflow()
    print("✅ PARMGraphWorkflow created successfully")
except Exception as e:
    print(f"❌ Failed to create workflow: {e}")
    sys.exit(1)

# Test 2: State creation and invocation
print("\n[TEST 2] Single Query Invocation")

test_state = {
    'patient_id': 'test-001',
    'message': 'Patient with chest pain and shortness of breath',
    'patient_data': {
        'name': 'Test Patient',
        'conditions': [],
        'medications': [],
        'allergies': [],
    },
    'triage_level': TriageLevel.ROUTINE,
    'draft_response': '',
    'critique_score': 0,
    'critique_feedback': '',
    'is_approved': False,
    'is_error': False,
    'error_message': '',
    'final_response': '',
    'response_status': 'pending',
    'reflection_iterations': 0,
    'reflection_history': [],
}

print(f"Input message: {test_state['message']}")
print(f"Patient ID: {test_state['patient_id']}")

try:
    result = workflow.invoke(test_state)
    print(f"\n✅ Workflow executed successfully")
    print(f"   Response Status: {result.get('response_status')}")
    print(f"   Is Error: {result.get('is_error')}")
    print(f"   Error Message: {result.get('error_message', 'None')}")
    print(f"   Draft Response Length: {len(result.get('draft_response', ''))}")
    print(f"   Triage Level: {result.get('triage_level')}")
    print(f"   Critique Score: {result.get('critique_score')}")
    print(f"   Is Approved: {result.get('is_approved')}")
    print(f"   Reflection Iterations: {result.get('reflection_iterations')}")
    
    if result.get('draft_response'):
        print(f"\n   Draft Response Preview:")
        print(f"   {result.get('draft_response')[:200]}...")
    else:
        print(f"\n   ⚠️  No draft response generated")
        
except Exception as e:
    print(f"❌ Workflow invocation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
