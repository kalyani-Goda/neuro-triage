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

    # Comprehensive drug-condition contraindications
    CONTRAINDICATIONS = {
        # Metformin contraindications
        "metformin": [
            "acute kidney injury", "severe dehydration", "renal impairment",
            "acute illness", "sepsis", "lactic acidosis", "liver disease",
            "severe heart failure", "acute heart attack", "stroke"
        ],
        # NSAID contraindications (including ibuprofen, naproxen, aspirin)
        "nsaid": [
            "renal impairment", "severe heart failure", "diabetes", "kidney disease",
            "hypertension", "cardiovascular disease", "asthma", "gastric ulcer",
            "bleeding disorder", "severe dehydration", "acute kidney injury"
        ],
        "ibuprofen": [
            "renal impairment", "severe heart failure", "diabetes", "kidney disease",
            "hypertension", "cardiovascular disease", "asthma", "gastric ulcer",
            "bleeding disorder", "severe dehydration"
        ],
        "naproxen": [
            "renal impairment", "severe heart failure", "diabetes", "kidney disease",
            "hypertension", "cardiovascular disease", "asthma", "gastric ulcer",
            "bleeding disorder", "severe dehydration"
        ],
        "aspirin": [
            "bleeding disorder", "active bleeding", "thrombocytopenia", "asthma",
            "gastric ulcer", "hemorrhage", "vitamin k deficiency"
        ],
        # ACE inhibitor contraindications
        "ace-inhibitor": [
            "pregnancy", "hyperkalemia", "high potassium", "renal artery stenosis",
            "angioedema", "severe renal failure", "acute kidney injury"
        ],
        # Warfarin contraindications
        "warfarin": [
            "thrombocytopenia", "active bleeding", "hemorrhage", "vitamin k",
            "low platelet count", "bleeding disorder", "recent surgery"
        ],
        # Beta-blocker contraindications
        "beta-blocker": [
            "asthma", "copd", "severe bradycardia", "atrioventricular block",
            "cardiogenic shock", "decompensated heart failure"
        ],
        # Calcium channel blocker contraindications
        "calcium channel blocker": [
            "severe hypotension", "cardiogenic shock", "acute myocardial infarction",
            "severe aortic stenosis"
        ],
        # Statins contraindications
        "statin": ["active liver disease", "elevated liver enzymes", "myopathy"],
        # SSRIs contraindications
        "ssri": ["maois", "monoamine oxidase", "tramadol"],
    }
    
    # Drug-drug interactions
    DRUG_INTERACTIONS = {
        # NSAIDs interactions with other medications
        ("nsaid", "aspirin"): "NSAID + Aspirin: Increased bleeding risk and GI ulceration",
        ("nsaid", "warfarin"): "NSAID + Warfarin: Increased bleeding risk",
        ("nsaid", "ace-inhibitor"): "NSAID + ACE inhibitor: Renal impairment risk",
        ("nsaid", "metformin"): "NSAID + Metformin: Lactic acidosis risk with renal impairment",
        
        # Warfarin interactions
        ("warfarin", "vitamin k"): "Warfarin + Vitamin K: Antagonizes anticoagulation",
        ("warfarin", "aspirin"): "Warfarin + Aspirin: Increased bleeding risk",
        ("warfarin", "nsaid"): "Warfarin + NSAID: Increased bleeding risk",
        
        # ACE inhibitor interactions
        ("ace-inhibitor", "potassium"): "ACE inhibitor + Potassium: Hyperkalemia risk",
        ("ace-inhibitor", "nsaid"): "ACE inhibitor + NSAID: Renal impairment",
        
        # Metformin interactions
        ("metformin", "contrast dye"): "Metformin + Contrast dye: Lactic acidosis risk",
        ("metformin", "alcohol"): "Metformin + Alcohol: Lactic acidosis risk",
        
        # SSRI interactions
        ("ssri", "maoi"): "SSRI + MAOI: Serotonin syndrome (dangerous)",
        ("ssri", "tramadol"): "SSRI + Tramadol: Serotonin syndrome risk",
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

        # Extract medications from text for more robust detection
        detected_meds = cls._extract_medications_from_text(med_lower)
        
        # Check drug-condition contraindications
        for med_pattern, contraindicated_conditions in cls.CONTRAINDICATIONS.items():
            if med_pattern in med_lower or any(med_pattern in dm for dm in detected_meds):
                for condition in patient_conditions:
                    condition_lower = condition.lower()
                    if any(c.lower() in condition_lower for c in contraindicated_conditions):
                        reason = (
                            f"CONTRAINDICATION: {med_pattern.title()} is contraindicated "
                            f"with {condition}"
                        )
                        logger.error(reason)
                        return False, reason

        # Check drug-drug interactions
        existing_meds_lower = [m.lower() for m in patient_medications]
        for (drug1, drug2), interaction_msg in cls.DRUG_INTERACTIONS.items():
            drug1_match = drug1 in med_lower or any(drug1 in dm for dm in detected_meds) or any(drug1 in m for m in existing_meds_lower)
            drug2_match = drug2 in med_lower or any(drug2 in dm for dm in detected_meds) or any(drug2 in m for m in existing_meds_lower)
            
            if drug1_match and drug2_match:
                logger.error(interaction_msg)
                return False, interaction_msg

        # Check for duplicate medication classes (NSAID combinations)
        nsaids = ["ibuprofen", "naproxen", "aspirin", "nsaid"]
        nsaid_count = sum(1 for nsaid in nsaids if any(nsaid in m.lower() for m in existing_meds_lower))
        if any(nsaid in med_lower for nsaid in nsaids) and nsaid_count > 0:
            reason = "CONTRAINDICATION: NSAID combination detected - increased GI and bleeding risk"
            logger.error(reason)
            return False, reason

        return True, "No contraindications detected"
    
    @classmethod
    def _extract_medications_from_text(cls, text: str) -> list:
        """Extract medication names from text."""
        medications = []
        med_keywords = [
            "naproxen", "ibuprofen", "aspirin", "metformin", "warfarin", 
            "lisinopril", "enalapril", "atorvastatin", "simvastatin",
            "fluoxetine", "sertraline", "tramadol", "codeine", "morphine",
            "vitamin k", "potassium", "magnesium", "calcium", "iron",
            "amoxicillin", "penicillin", "antibiotics", "steroids",
        ]
        for med in med_keywords:
            if med in text:
                medications.append(med)
        return medications

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
