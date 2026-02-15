"""Patient data management and retrieval."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from src.memory.models import (
    Patient,
    PatientMedicalHistory,
    Medication,
    Allergy,
)

logger = logging.getLogger(__name__)


class PatientManager:
    """Manager for patient data operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def get_patient(self, patient_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve complete patient profile."""
        try:
            patient = self.session.query(Patient).filter_by(patient_id=patient_id).first()
            if not patient:
                logger.warning(f"Patient not found: {patient_id}")
                return None

            # Get related data
            medical_history = self.session.query(PatientMedicalHistory).filter_by(
                patient_id=patient_id
            ).all()
            medications = self.session.query(Medication).filter_by(patient_id=patient_id).all()
            allergies = self.session.query(Allergy).filter_by(patient_id=patient_id).all()

            return {
                "patient_id": str(patient.patient_id),
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
                "email": patient.email,
                "phone": patient.phone,
                "address": patient.address,
                "medical_history": [
                    {
                        "condition": h.condition_name,
                        "status": h.status,
                        "severity": h.severity_level,
                        "diagnosis_date": h.diagnosis_date.isoformat() if h.diagnosis_date else None,
                    }
                    for h in medical_history
                ],
                "medications": [
                    {
                        "name": m.medication_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "reason": m.reason_prescribed,
                    }
                    for m in medications
                ],
                "allergies": [
                    {
                        "allergen": a.allergen,
                        "reaction_type": a.reaction_type,
                        "severity": a.severity,
                    }
                    for a in allergies
                ],
            }
        except Exception as e:
            logger.error(f"Error retrieving patient: {e}")
            return None

    def create_patient(self, patient_data: Dict[str, Any]) -> Optional[UUID]:
        """Create a new patient record."""
        try:
            patient = Patient(
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                date_of_birth=patient_data["date_of_birth"],
                gender=patient_data.get("gender"),
                email=patient_data.get("email"),
                phone=patient_data.get("phone"),
                address=patient_data.get("address"),
                city=patient_data.get("city"),
                state=patient_data.get("state"),
                zip_code=patient_data.get("zip_code"),
            )
            self.session.add(patient)
            self.session.commit()
            logger.info(f"Patient created: {patient.patient_id}")
            return patient.patient_id
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            self.session.rollback()
            return None

    def add_medical_condition(
        self,
        patient_id: UUID,
        condition_name: str,
        status: str = "active",
        severity: str = "moderate",
    ) -> bool:
        """Add a medical condition to patient history."""
        try:
            history = PatientMedicalHistory(
                patient_id=patient_id,
                condition_name=condition_name,
                status=status,
                severity_level=severity,
            )
            self.session.add(history)
            self.session.commit()
            logger.info(f"Condition added to patient {patient_id}: {condition_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding medical condition: {e}")
            self.session.rollback()
            return False

    def add_medication(
        self,
        patient_id: UUID,
        medication_name: str,
        dosage: str,
        frequency: str,
        reason: str,
    ) -> bool:
        """Add a medication to patient record."""
        try:
            medication = Medication(
                patient_id=patient_id,
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                reason_prescribed=reason,
            )
            self.session.add(medication)
            self.session.commit()
            logger.info(f"Medication added to patient {patient_id}: {medication_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding medication: {e}")
            self.session.rollback()
            return False

    def add_allergy(
        self,
        patient_id: UUID,
        allergen: str,
        reaction_type: str,
        severity: str = "moderate",
    ) -> bool:
        """Add an allergy to patient record."""
        try:
            allergy = Allergy(
                patient_id=patient_id,
                allergen=allergen,
                reaction_type=reaction_type,
                severity=severity,
            )
            self.session.add(allergy)
            self.session.commit()
            logger.info(f"Allergy added to patient {patient_id}: {allergen}")
            return True
        except Exception as e:
            logger.error(f"Error adding allergy: {e}")
            self.session.rollback()
            return False
