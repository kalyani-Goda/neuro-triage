"""Safety guardrails and compliance checks."""

import logging
from typing import Dict, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TriageLevel(str, Enum):
    """Triage severity levels."""

    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"


class SafetyGuardrail:
    """Safety guardrails for clinical decisions."""

    # Emergency keywords that trigger immediate escalation
    EMERGENCY_KEYWORDS = {
        "chest pain",
        "difficulty breathing",
        "severe bleeding",
        "loss of consciousness",
        "stroke",
        "sepsis",
        "anaphylaxis",
        "cardiac arrest",
        "acute myocardial infarction",
        "pulmonary embolism",
        "severe trauma",
        "unconscious",
        "unresponsive",
        "critical",
        "life-threatening",
        "911",
        "emergency",
    }

    # Urgent keywords
    URGENT_KEYWORDS = {
        "severe pain",
        "persistent vomiting",
        "high fever",
        "severe headache",
        "acute infection",
        "diabetic emergency",
        "severe allergic reaction",
        "broken bone",
        "deep laceration",
        "abdominal pain",
    }

    # Contraindicated combinations (medication + condition)
    CONTRAINDICATIONS = {
        "metformin": ["acute kidney injury", "severe dehydration"],
        "nsaid": ["renal impairment", "severe heart failure"],
        "ace-inhibitor": ["pregnancy", "hyperkalemia"],
        "warfarin": ["thrombocytopenia", "active bleeding"],
    }

    @classmethod
    def classify_triage(cls, user_input: str, patient_data: Dict = None) -> TriageLevel:
        """Classify patient urgency from input text and history."""
        user_input_lower = user_input.lower()

        # Check emergency keywords
        for keyword in cls.EMERGENCY_KEYWORDS:
            if keyword in user_input_lower:
                logger.warning(f"Emergency detected: {keyword}")
                return TriageLevel.EMERGENCY

        # Check urgent keywords
        for keyword in cls.URGENT_KEYWORDS:
            if keyword in user_input_lower:
                logger.info(f"Urgent case detected: {keyword}")
                return TriageLevel.URGENT

        # Default to routine
        return TriageLevel.ROUTINE

    @classmethod
    def check_contraindications(
        cls,
        recommended_medication: str,
        patient_conditions: list,
        patient_medications: list,
    ) -> Tuple[bool, str]:
        """Check for dangerous drug-condition or drug-drug interactions."""
        med_lower = recommended_medication.lower()

        # Check drug-condition contraindications
        for med_pattern, contraindicated_conditions in cls.CONTRAINDICATIONS.items():
            if med_pattern in med_lower:
                for condition in patient_conditions:
                    if any(c in condition.lower() for c in contraindicated_conditions):
                        reason = (
                            f"CONTRAINDICATION: {recommended_medication} is contraindicated "
                            f"with {condition}"
                        )
                        logger.error(reason)
                        return False, reason

        # Check for duplicate medication classes
        # (simplified - in production, use proper drug interaction database)
        existing_meds_lower = [m.lower() for m in patient_medications]
        nsaids = ["ibuprofen", "naproxen", "aspirin"]
        recommended_lower = recommended_medication.lower()

        if any(nsaid in recommended_lower for nsaid in nsaids):
            if any(nsaid in med for nsaid in nsaids for med in existing_meds_lower):
                reason = f"CONTRAINDICATION: NSAID combination detected"
                logger.error(reason)
                return False, reason

        return True, "No contraindications detected"

    @classmethod
    def validate_response(cls, response: str, safety_score: int) -> Tuple[bool, str]:
        """Validate response meets safety thresholds."""
        from src.config import settings

        if safety_score < settings.safety_score_min:
            reason = f"Safety score {safety_score} below threshold {settings.safety_score_min}"
            logger.warning(reason)
            return False, reason

        # Check for dangerous language patterns
        dangerous_patterns = [
            "ignore your doctor",
            "stop taking",
            "don't go to hospital",
            "no need for emergency",
            "untested remedy",
        ]

        for pattern in dangerous_patterns:
            if pattern.lower() in response.lower():
                reason = f"Dangerous language detected: '{pattern}'"
                logger.error(reason)
                return False, reason

        return True, "Response passes safety validation"

    @classmethod
    def get_emergency_response(cls) -> str:
        """Get hard-coded emergency response."""
        return (
            "🚨 EMERGENCY ALERT 🚨\n\n"
            "Your symptoms require IMMEDIATE medical attention.\n"
            "CALL 911 OR GO TO THE NEAREST EMERGENCY ROOM IMMEDIATELY.\n\n"
            "Do not wait. Do not delay.\n"
            "Your healthcare provider has been alerted.\n"
            "Emergency services are recommended for your safety."
        )
