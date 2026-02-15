#!/usr/bin/env python3
"""
Test hallucination detection functionality.
"""

import sys
sys.path.insert(0, '/Users/kalyani/Desktop/Projects/neuro-triage')

from src.safety.hallucination_detector import HallucinationDetector

print("=" * 80)
print("HALLUCINATION DETECTION TEST")
print("=" * 80)
print()

test_cases = [
    {
        "name": "Hallucination 1: Fictitious Syndrome",
        "response": "Fictitious Syndrome Z is a rare condition that affects the quantum nervous system. It requires treatment with Imaginex medication.",
        "should_detect": True,
    },
    {
        "name": "Hallucination 2: Made-up Drug",
        "response": "The best treatment for this condition is Imaginex, a novel pharmaceutical compound that works on the cellular level.",
        "should_detect": True,
    },
    {
        "name": "Hallucination 3: Fake Test",
        "response": "The BloodHarmony Panel is a comprehensive test that measures your body's harmony levels and chakra alignment.",
        "should_detect": True,
    },
    {
        "name": "Legitimate Response 1: Real Conditions",
        "response": "Based on your symptoms, you may have diabetes or hypertension. I recommend consulting with your doctor for proper diagnosis.",
        "should_detect": False,
    },
    {
        "name": "Legitimate Response 2: Real Drugs",
        "response": "Common treatments include aspirin, ibuprofen, or naproxen for pain management. Always consult your healthcare provider.",
        "should_detect": False,
    },
    {
        "name": "Legitimate Response 3: Real Tests",
        "response": "Your doctor may order an MRI, CT scan, or blood test to confirm the diagnosis.",
        "should_detect": False,
    },
    {
        "name": "Borderline: Made-up sounding term",
        "response": "Some practitioners claim Quantum Healing can cure disease, but this lacks scientific evidence.",
        "should_detect": True,
    },
]

passed = 0
failed = 0

for test in test_cases:
    print(f"Test: {test['name']}")
    print(f"Response: {test['response'][:80]}...")
    
    is_hallucinating, feedback, terms = HallucinationDetector.detect_hallucinations(
        response=test['response']
    )
    
    expected = test['should_detect']
    
    if is_hallucinating == expected:
        print(f"✅ PASS")
        passed += 1
    else:
        print(f"❌ FAIL - Expected hallucination={expected}, got {is_hallucinating}")
        failed += 1
    
    if is_hallucinating:
        print(f"   Suspicious terms: {terms}")
        print(f"   Feedback: {feedback}")
    
    print()

print("=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 80)

if failed > 0:
    sys.exit(1)
