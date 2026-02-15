#!/usr/bin/env python3
"""Simple integration test for hallucination detection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from safety.hallucination_detector import HallucinationDetector

def test_hallucination_detection_integration():
    """Test hallucination detection with mock responses."""
    print("\n" + "="*80)
    print("HALLUCINATION DETECTION INTEGRATION TEST")
    print("="*80)
    
    hallucination_detector = HallucinationDetector()
    
    test_cases = [
        {
            "name": "Fictitious Syndrome",
            "query": "What is Fictitious Syndrome Z?",
            "response": "Fictitious Syndrome Z is a rare condition that affects the quantum nervous system. It typically causes hallucinations and unusual sensory perceptions.",
            "expected_hallucination": True,
        },
        {
            "name": "Made-up Drug",
            "query": "Tell me about the drug Imaginex",
            "response": "Imaginex is a novel pharmaceutical compound developed for treating imaginary illnesses. It's not approved by any regulatory agency.",
            "expected_hallucination": True,
        },
        {
            "name": "Fake Medical Test",
            "query": "What is the BloodHarmony Panel test?",
            "response": "The BloodHarmony Panel is a comprehensive test that measures your body's harmony through various biomarkers. It costs $500 per test.",
            "expected_hallucination": True,
        },
        {
            "name": "Real Condition",
            "query": "What is diabetes mellitus?",
            "response": "Diabetes mellitus is a chronic disease characterized by high blood glucose levels. Types include Type 1 and Type 2. Treatment includes diet, exercise, and medication.",
            "expected_hallucination": False,
        },
        {
            "name": "Real Drug",
            "query": "Tell me about aspirin",
            "response": "Aspirin is a common pain reliever and anti-inflammatory medication. It's used for headaches, fevers, and heart disease prevention.",
            "expected_hallucination": False,
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}: {test['name']}")
        print(f"Query: {test['query']}")
        
        try:
            response = test['response']
            
            # Detect hallucinations
            is_hallucinating, feedback, suspected_terms = hallucination_detector.detect_hallucinations(response)
            
            print(f"Response: {response[:80]}...")
            print(f"Has hallucinations: {is_hallucinating}")
            if suspected_terms:
                print(f"Suspected terms: {suspected_terms}")
            print(f"Feedback: {feedback[:80]}...")
            
            # Check if hallucination detection matches expectation
            detected_hallucination = is_hallucinating
            expected_hallucination = test['expected_hallucination']
            
            if detected_hallucination == expected_hallucination:
                print(f"✅ PASS")
                passed += 1
            else:
                print(f"❌ FAIL - Expected hallucination={expected_hallucination}, got {detected_hallucination}")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_hallucination_detection_integration()
    sys.exit(0 if success else 1)
