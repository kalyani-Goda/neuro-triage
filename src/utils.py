"""Utility functions."""

import hashlib
import json
from typing import Dict, Any
from datetime import datetime


def hash_input(text: str) -> str:
    """Generate hash of input for caching."""
    return hashlib.md5(text.encode()).hexdigest()


def format_patient_context(patient_data: Dict[str, Any]) -> str:
    """Format patient data for LLM context."""
    if isinstance(patient_data, dict) and "error" in patient_data:
        return "[Patient data unavailable]"
    
    parts = []
    
    if patient_data.get("first_name"):
        parts.append(f"Patient: {patient_data['first_name']} {patient_data.get('last_name', '')}")
    
    if patient_data.get("medical_history"):
        conditions = [h["condition"] for h in patient_data["medical_history"]]
        parts.append(f"Conditions: {', '.join(conditions)}")
    
    if patient_data.get("medications"):
        meds = [m["name"] for m in patient_data["medications"]]
        parts.append(f"Medications: {', '.join(meds)}")
    
    if patient_data.get("allergies"):
        allergies = [a["allergen"] for a in patient_data["allergies"]]
        parts.append(f"Allergies: {', '.join(allergies)}")
    
    return "\n".join(parts) or "[No patient data]"


def get_timestamp() -> str:
    """Get ISO format timestamp."""
    return datetime.utcnow().isoformat()


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback."""
    try:
        return json.loads(json_str)
    except:
        return default
