"""ETL script for synthetic patient generation and loading."""

import json
import logging
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
import random

from src.infrastructure.database import get_session
from src.memory.patient_manager import PatientManager
from src.memory.models import Patient, PatientMedicalHistory, Medication, Allergy

logger = logging.getLogger(__name__)


class SyntheticPatientGenerator:
    """Generate synthetic FHIR-like patient data."""

    COMMON_CONDITIONS = [
        ("Hypertension", "active", "moderate"),
        ("Type 2 Diabetes", "active", "moderate"),
        ("Asthma", "active", "mild"),
        ("Hyperlipidemia", "active", "mild"),
        ("Chronic Obstructive Pulmonary Disease", "active", "moderate"),
        ("Depression", "active", "mild"),
        ("Arthritis", "active", "moderate"),
        ("Gastroesophageal Reflux Disease", "active", "mild"),
        ("Hypothyroidism", "active", "mild"),
        ("Coronary Artery Disease", "active", "severe"),
    ]

    COMMON_MEDICATIONS = [
        ("Lisinopril", "10mg", "Once daily", "Hypertension"),
        ("Metformin", "500mg", "Twice daily", "Type 2 Diabetes"),
        ("Albuterol", "As needed", "As needed", "Asthma"),
        ("Atorvastatin", "40mg", "Once daily", "High cholesterol"),
        ("Sertraline", "50mg", "Once daily", "Depression"),
        ("Omeprazole", "20mg", "Once daily", "GERD"),
        ("Levothyroxine", "75mcg", "Once daily", "Hypothyroidism"),
        ("Aspirin", "81mg", "Once daily", "Heart health"),
    ]

    COMMON_ALLERGIES = [
        ("Penicillin", "Rash", "moderate"),
        ("Sulfonamides", "Anaphylaxis", "severe"),
        ("Latex", "Contact dermatitis", "mild"),
        ("Shellfish", "Anaphylaxis", "severe"),
        ("Peanuts", "Anaphylaxis", "severe"),
        ("NSAIDs", "Stomach upset", "mild"),
    ]

    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer",
        "Michael", "Linda", "William", "Barbara", "David", "Susan",
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
        "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    ]

    @staticmethod
    def generate_patient(patient_num: int) -> Dict[str, Any]:
        """Generate a single synthetic patient."""
        first_name = random.choice(SyntheticPatientGenerator.FIRST_NAMES)
        last_name = random.choice(SyntheticPatientGenerator.LAST_NAMES)

        # Random age between 18 and 85
        age = random.randint(18, 85)
        dob = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))

        patient = {
            "patient_id": str(uuid4()),
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob.date(),
            "gender": random.choice(["M", "F"]),
            "email": f"{first_name.lower()}.{last_name.lower()}{patient_num}@example.com",
            "phone": f"555-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 9999)} Main St",
            "city": random.choice(["Boston", "New York", "Los Angeles", "Chicago", "Houston"]),
            "state": random.choice(["MA", "NY", "CA", "IL", "TX"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "medical_history": [],
            "medications": [],
            "allergies": [],
        }

        # Add 1-3 medical conditions
        num_conditions = random.randint(1, 3)
        for _ in range(num_conditions):
            condition, status, severity = random.choice(SyntheticPatientGenerator.COMMON_CONDITIONS)
            patient["medical_history"].append({
                "condition_name": condition,
                "status": status,
                "severity_level": severity,
            })

        # Add 0-2 medications
        num_meds = random.randint(0, 2)
        for _ in range(num_meds):
            med_name, dosage, frequency, reason = random.choice(SyntheticPatientGenerator.COMMON_MEDICATIONS)
            patient["medications"].append({
                "medication_name": med_name,
                "dosage": dosage,
                "frequency": frequency,
                "reason_prescribed": reason,
            })

        # Add 0-1 allergies
        if random.random() < 0.4:
            allergen, reaction, severity = random.choice(SyntheticPatientGenerator.COMMON_ALLERGIES)
            patient["allergies"].append({
                "allergen": allergen,
                "reaction_type": reaction,
                "severity": severity,
            })

        return patient


class PatientETL:
    """ETL process for loading patient data."""

    @staticmethod
    def load_synthetic_patients(count: int = 100) -> int:
        """Generate and load synthetic patients to database."""
        logger.info(f"Generating {count} synthetic patients...")

        session = get_session()
        manager = PatientManager(session)
        loaded_count = 0

        try:
            for i in range(count):
                patient_data = SyntheticPatientGenerator.generate_patient(i)

                # Create patient
                patient_id = manager.create_patient({
                    "first_name": patient_data["first_name"],
                    "last_name": patient_data["last_name"],
                    "date_of_birth": patient_data["date_of_birth"],
                    "gender": patient_data["gender"],
                    "email": patient_data["email"],
                    "phone": patient_data["phone"],
                    "address": patient_data["address"],
                    "city": patient_data["city"],
                    "state": patient_data["state"],
                    "zip_code": patient_data["zip_code"],
                })

                if not patient_id:
                    continue

                # Add medical history
                for condition in patient_data.get("medical_history", []):
                    manager.add_medical_condition(
                        patient_id=patient_id,
                        condition_name=condition["condition_name"],
                        status=condition.get("status", "active"),
                        severity=condition.get("severity_level", "moderate"),
                    )

                # Add medications
                for med in patient_data.get("medications", []):
                    manager.add_medication(
                        patient_id=patient_id,
                        medication_name=med["medication_name"],
                        dosage=med.get("dosage", ""),
                        frequency=med.get("frequency", ""),
                        reason=med.get("reason_prescribed", ""),
                    )

                # Add allergies
                for allergy in patient_data.get("allergies", []):
                    manager.add_allergy(
                        patient_id=patient_id,
                        allergen=allergy["allergen"],
                        reaction_type=allergy.get("reaction_type", ""),
                        severity=allergy.get("severity", "moderate"),
                    )

                loaded_count += 1
                if (i + 1) % 10 == 0:
                    logger.info(f"Loaded {i + 1}/{count} patients")

        except Exception as e:
            logger.error(f"ETL error: {e}")
        finally:
            session.close()

        logger.info(f"Successfully loaded {loaded_count} patients")
        return loaded_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    PatientETL.load_synthetic_patients(count=100)
