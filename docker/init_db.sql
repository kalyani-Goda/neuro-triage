-- Initialize PostgreSQL Database for Neuro-Triage

-- Create Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Patient Medical History
CREATE TABLE IF NOT EXISTS patient_medical_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    condition_name VARCHAR(255) NOT NULL,
    diagnosis_date DATE,
    status VARCHAR(50), -- active, resolved, inactive
    severity_level VARCHAR(20), -- mild, moderate, severe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Medications Table
CREATE TABLE IF NOT EXISTS medications (
    medication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    start_date DATE,
    end_date DATE,
    reason_prescribed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Allergies Table
CREATE TABLE IF NOT EXISTS allergies (
    allergy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    allergen VARCHAR(255) NOT NULL,
    reaction_type VARCHAR(100),
    severity VARCHAR(20), -- mild, moderate, severe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Consultation Sessions
CREATE TABLE IF NOT EXISTS consultation_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    triage_level VARCHAR(20), -- emergency, urgent, routine
    initial_complaint TEXT,
    final_assessment TEXT,
    draft_response TEXT,
    critique_score INTEGER,
    status VARCHAR(50), -- active, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Conversation Logs
CREATE TABLE IF NOT EXISTS conversation_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES consultation_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50), -- user, assistant, system
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reflection_details JSONB
);

-- Create Audit Log (for safety & compliance)
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type VARCHAR(100),
    patient_id UUID REFERENCES patients(patient_id),
    session_id UUID REFERENCES consultation_sessions(session_id),
    details JSONB,
    user_role VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patient_history_patient_id ON patient_medical_history(patient_id);
CREATE INDEX idx_medications_patient_id ON medications(patient_id);
CREATE INDEX idx_allergies_patient_id ON allergies(patient_id);
CREATE INDEX idx_sessions_patient_id ON consultation_sessions(patient_id);
CREATE INDEX idx_sessions_triage_level ON consultation_sessions(triage_level);
CREATE INDEX idx_conversation_logs_session_id ON conversation_logs(session_id);
CREATE INDEX idx_audit_logs_patient_id ON audit_logs(patient_id);

-- Grant Permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO neuro_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO neuro_user;
