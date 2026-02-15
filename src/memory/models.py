"""SQLAlchemy ORM models for Neuro-Triage."""

from sqlalchemy import Column, String, DateTime, Text, Integer, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from src.infrastructure.database import Base


class Patient(Base):
    """Patient model."""

    __tablename__ = "patients"

    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientMedicalHistory(Base):
    """Patient medical history model."""

    __tablename__ = "patient_medical_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"), nullable=False)
    condition_name = Column(String(255), nullable=False)
    diagnosis_date = Column(Date)
    status = Column(String(50))  # active, resolved, inactive
    severity_level = Column(String(20))  # mild, moderate, severe
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Medication(Base):
    """Medication model."""

    __tablename__ = "medications"

    medication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"), nullable=False)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    reason_prescribed = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Allergy(Base):
    """Allergy model."""

    __tablename__ = "allergies"

    allergy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"), nullable=False)
    allergen = Column(String(255), nullable=False)
    reaction_type = Column(String(100))
    severity = Column(String(20))  # mild, moderate, severe
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsultationSession(Base):
    """Consultation session model."""

    __tablename__ = "consultation_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    triage_level = Column(String(20))  # emergency, urgent, routine
    initial_complaint = Column(Text)
    final_assessment = Column(Text)
    draft_response = Column(Text)
    critique_score = Column(Integer)
    status = Column(String(50), default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationLog(Base):
    """Conversation log model."""

    __tablename__ = "conversation_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("consultation_sessions.session_id"), nullable=False)
    role = Column(String(50))  # user, assistant, system
    message_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reflection_details = Column(JSON)


class AuditLog(Base):
    """Audit log for compliance and safety."""

    __tablename__ = "audit_logs"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(100))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("consultation_sessions.session_id"))
    details = Column(JSON)
    user_role = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
