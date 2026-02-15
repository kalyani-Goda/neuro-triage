"""
PHASE 7 — Real Data ETL Pipeline
Ingest real clinical datasets: MedQuAD, Synthea, PDF documents
Follows paper-style data provenance and quality assurance
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config import Settings
from src.memory.models import (
    Patient, PatientMedicalHistory, Medication, Allergy
)

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Real data ingestion with quality assurance and provenance tracking."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = create_engine(settings.database_url)
        self.processed_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    def log_summary(self) -> Dict[str, Any]:
        """Generate ETL execution summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "records_processed": self.processed_count,
            "errors": self.error_count,
            "success_rate": (self.processed_count - self.error_count) / max(1, self.processed_count),
        }


class MedQuADETL(ETLPipeline):
    """
    MedQuAD ETL Pipeline
    Source: https://github.com/abachaa/MedQuAD
    Format: XML Q&A pairs for medical conditions
    Usage: Medical knowledge base for document retrieval
    """

    def ingest_medquad(self, medquad_dir: str) -> List[Dict[str, Any]]:
        """
        Ingest MedQuAD dataset into Qdrant vector database.
        
        Expected directory structure:
        medquad_dir/
        ├── GARD/                    (Genetic and Rare Diseases)
        ├── NCCIH/                   (National Center for Complementary & Integrative Health)
        ├── NHLBI/                   (National Heart, Lung, and Blood Institute)
        ├── NCI/                     (National Cancer Institute)
        ├── NINDS/                   (National Institute of Neurological Disorders)
        ├── PlainLanguage/           (Plain language summaries)
        └── Rare-Diseases/           (Additional rare disease content)
        
        Each XML file contains:
        - Question (medical query)
        - Answer (authoritative response)
        - Category (disease/condition classification)
        """
        documents = []
        medquad_path = Path(medquad_dir)

        if not medquad_path.exists():
            logger.warning(f"MedQuAD directory not found: {medquad_dir}")
            logger.info("To use MedQuAD: git clone https://github.com/abachaa/MedQuAD {medquad_dir}")
            return documents

        for xml_file in medquad_path.rglob("*.xml"):
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Extract Q&A pairs
                for item in root.findall(".//QAPair"):
                    question = item.find("Question")
                    answer = item.find("Answer")

                    if question is not None and answer is not None:
                        q_text = question.text or ""
                        a_text = answer.text or ""

                        if q_text.strip() and a_text.strip():
                            # Create document for Qdrant ingestion
                            doc = {
                                "source": "MedQuAD",
                                "file": xml_file.name,
                                "category": xml_file.parent.name,
                                "question": q_text.strip(),
                                "answer": a_text.strip(),
                                "content": f"Q: {q_text}\nA: {a_text}",
                                "metadata": {
                                    "source_file": str(xml_file),
                                    "ingest_date": datetime.now().isoformat(),
                                    "content_hash": hashlib.md5(a_text.encode()).hexdigest(),
                                },
                            }
                            documents.append(doc)
                            self.processed_count += 1

            except Exception as e:
                logger.error(f"Error processing {xml_file}: {e}")
                self.error_count += 1

        logger.info(f"MedQuAD: Ingested {self.processed_count} Q&A pairs from {medquad_path}")
        return documents


class SyntheaETL(ETLPipeline):
    """
    Synthea ETL Pipeline
    Source: https://github.com/synthetichealth/synthea
    Format: CSV files with synthetic EHR data
    Usage: Realistic patient histories, medications, conditions
    
    Generated files:
    - patients.csv: Demographics, vital stats
    - encounters.csv: Clinical visits
    - conditions.csv: ICD-10 diagnoses
    - medications.csv: Prescriptions
    - allergies.csv: Documented allergies
    """

    def ingest_synthea(self, synthea_dir: str) -> tuple[int, int]:
        """
        Load Synthea synthetic patient data into PostgreSQL.
        
        Directory structure:
        synthea_output/
        ├── csv/
        │   ├── patients.csv
        │   ├── encounters.csv
        │   ├── conditions.csv
        │   ├── medications.csv
        │   └── allergies.csv
        └── fhir/  (alternative FHIR JSON format)
        """
        synthea_path = Path(synthea_dir)
        csv_dir = synthea_path / "csv"

        if not csv_dir.exists():
            logger.warning(f"Synthea CSV directory not found: {csv_dir}")
            logger.info("To use Synthea: https://github.com/synthetichealth/synthea")
            logger.info("  1. Clone repository: git clone https://github.com/synthetichealth/synthea")
            logger.info("  2. Run: cd synthea && ./run_synthea.sh -p 100  # 100 patients")
            logger.info("  3. Output: output/csv/ directory created")
            return 0, 0

        session = Session(self.engine)
        try:
            # Load patients
            if (csv_dir / "patients.csv").exists():
                patients_df = pd.read_csv(csv_dir / "patients.csv")
                logger.info(f"Synthea: Loading {len(patients_df)} patients")

                for _, row in patients_df.iterrows():
                    try:
                        patient = Patient(
                            id=str(row["Id"]),
                            first_name=row.get("FIRST", ""),
                            last_name=row.get("LAST", ""),
                            date_of_birth=pd.to_datetime(row.get("BIRTHDATE", None)),
                            gender=row.get("GENDER", "").upper()[0] if row.get("GENDER") else "U",
                            address=row.get("ADDRESS", ""),
                            phone=row.get("PHONE", ""),
                            email=row.get("EMAIL", ""),
                        )
                        session.add(patient)
                        self.processed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing patient {row.get('Id')}: {e}")
                        self.error_count += 1

                session.commit()

            # Load conditions
            if (csv_dir / "conditions.csv").exists():
                conditions_df = pd.read_csv(csv_dir / "conditions.csv")
                logger.info(f"Synthea: Loading {len(conditions_df)} conditions")

                for _, row in conditions_df.iterrows():
                    try:
                        record = PatientMedicalHistory(
                            patient_id=str(row["PATIENT"]),
                            condition_name=row.get("DESCRIPTION", ""),
                            status="active",
                        )
                        session.add(record)
                    except Exception as e:
                        logger.error(f"Error processing condition: {e}")
                        self.error_count += 1

                session.commit()

            # Load medications
            if (csv_dir / "medications.csv").exists():
                meds_df = pd.read_csv(csv_dir / "medications.csv")
                logger.info(f"Synthea: Loading {len(meds_df)} medications")

                for _, row in meds_df.iterrows():
                    try:
                        med = Medication(
                            patient_id=str(row["PATIENT"]),
                            name=row.get("DESCRIPTION", ""),
                            rxnorm_code=row.get("CODE", ""),
                            start_date=pd.to_datetime(row.get("START", None)),
                            status="active",
                        )
                        session.add(med)
                    except Exception as e:
                        logger.error(f"Error processing medication: {e}")
                        self.error_count += 1

                session.commit()

            # Load allergies
            if (csv_dir / "allergies.csv").exists():
                allergies_df = pd.read_csv(csv_dir / "allergies.csv")
                logger.info(f"Synthea: Loading {len(allergies_df)} allergies")

                for _, row in allergies_df.iterrows():
                    try:
                        allergy = Allergy(
                            patient_id=str(row["PATIENT"]),
                            allergen=row.get("DESCRIPTION", ""),
                            reaction_type=row.get("REACTION", ""),
                            severity=row.get("SEVERITY", "Unknown"),
                        )
                        session.add(allergy)
                    except Exception as e:
                        logger.error(f"Error processing allergy: {e}")
                        self.error_count += 1

                session.commit()

            logger.info(f"Synthea: Successfully ingested {self.processed_count} records")
            return self.processed_count, self.error_count

        finally:
            session.close()


class PDFDocumentETL(ETLPipeline):
    """
    PDF Document ETL Pipeline
    Ingest medical literature, clinical guidelines, policy documents
    Extract text and embed into Qdrant for semantic retrieval
    """

    def ingest_pdf_documents(self, pdf_dir: str, vector_store) -> List[Dict[str, Any]]:
        """
        Extract and index PDF documents.
        
        Directory structure:
        docs/
        ├── guidelines/        (Clinical practice guidelines)
        ├── literature/        (Research papers)
        ├── policies/          (Hospital/institutional policies)
        └── training/          (Training materials)
        """
        documents = []
        pdf_path = Path(pdf_dir)

        if not pdf_path.exists():
            logger.warning(f"PDF directory not found: {pdf_dir}")
            return documents

        # Optional: Install PyPDF2 for PDF parsing
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return documents

        for pdf_file in pdf_path.rglob("*.pdf"):
            try:
                reader = PdfReader(pdf_file)
                text = ""

                for page_num, page in enumerate(reader.pages):
                    text += page.extract_text() or ""

                if text.strip():
                    # Split into chunks (1000 char chunks with 100 char overlap)
                    chunks = self._chunk_text(text, chunk_size=1000, overlap=100)

                    for chunk_idx, chunk in enumerate(chunks):
                        doc = {
                            "source": "PDF",
                            "file": pdf_file.name,
                            "category": pdf_file.parent.name,
                            "content": chunk,
                            "metadata": {
                                "source_file": str(pdf_file),
                                "page_count": len(reader.pages),
                                "chunk_number": chunk_idx,
                                "ingest_date": datetime.now().isoformat(),
                                "content_hash": hashlib.md5(chunk.encode()).hexdigest(),
                            },
                        }
                        documents.append(doc)
                        self.processed_count += 1

            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                self.error_count += 1

        logger.info(f"PDF: Ingested {self.processed_count} document chunks from {pdf_path}")
        return documents

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])
        return chunks


class CSVDatasetETL(ETLPipeline):
    """
    Generic CSV Dataset ETL Pipeline
    Load any CSV-formatted clinical data (vendor exports, research datasets, etc.)
    """

    def ingest_csv_dataset(
        self,
        csv_file: str,
        model_class,
        field_mapping: Dict[str, str],
    ) -> tuple[int, int]:
        """
        Generic CSV loader with field mapping.
        
        Args:
            csv_file: Path to CSV file
            model_class: SQLAlchemy model (Patient, MedicalRecord, etc.)
            field_mapping: Dict mapping CSV column → model field
                Example: {"PatientID": "id", "FirstName": "first_name"}
        """
        csv_path = Path(csv_file)

        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_file}")
            return 0, 0

        session = Session(self.engine)
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"CSV: Loading {len(df)} records from {csv_path.name}")

            for _, row in df.iterrows():
                try:
                    # Build kwargs from field mapping
                    kwargs = {}
                    for csv_col, model_field in field_mapping.items():
                        if csv_col in row.index:
                            value = row[csv_col]
                            # Handle null/NaN values
                            if pd.notna(value):
                                kwargs[model_field] = value

                    # Create and add model instance
                    obj = model_class(**kwargs)
                    session.add(obj)
                    self.processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing row: {e}")
                    self.error_count += 1

            session.commit()
            logger.info(f"CSV: Successfully ingested {self.processed_count} records")
            return self.processed_count, self.error_count

        finally:
            session.close()


# ============================================================================
# USAGE EXAMPLES (Template for users)
# ============================================================================

"""
QUICK START: Real Data Ingestion

1. MedQuAD (Medical Q&A Database)
   ```python
   from scripts.data_ingestion_etl import MedQuADETL
   
   pipeline = MedQuADETL(settings)
   documents = pipeline.ingest_medquad("data/medquad")
   # → Documents ready for Qdrant vectorization
   ```

2. Synthea (Synthetic EHR Data)
   ```python
   from scripts.data_ingestion_etl import SyntheaETL
   
   pipeline = SyntheaETL(settings)
   count, errors = pipeline.ingest_synthea("data/synthea_output")
   # → Patients, conditions, medications loaded into PostgreSQL
   ```

3. PDF Documents (Guidelines, Literature)
   ```python
   from scripts.data_ingestion_etl import PDFDocumentETL
   
   pipeline = PDFDocumentETL(settings)
   documents = pipeline.ingest_pdf_documents("data/docs", vector_store)
   # → Documents chunked and ready for Qdrant
   ```

4. Generic CSV Data
   ```python
   from scripts.data_ingestion_etl import CSVDatasetETL
   
   pipeline = CSVDatasetETL(settings)
   mapping = {"PatientID": "id", "FirstName": "first_name", "DOB": "date_of_birth"}
   count, errors = pipeline.ingest_csv_dataset("data/patients.csv", Patient, mapping)
   ```

DATA SOURCES:
- MedQuAD: https://github.com/abachaa/MedQuAD
- Synthea: https://github.com/synthetichealth/synthea
- Medical Literature: PubMed, arXiv, Google Scholar
- Clinical Guidelines: NIH, CDC, JAMA, Lancet
- EHR Exports: HL7 FHIR format, vendor-specific CSV
"""
