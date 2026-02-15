# PHASE 7: Evaluation & Real Data Ingestion

This directory contains tools for Phase 7 of the Neuro-Triage paper framework:
- **Quantitative Rigor**: Comprehensive evaluation metrics and benchmarks
- **Real Data Integration**: ETL pipelines for medical datasets

## 📊 Evaluation Components

### Quick Start: Run Evaluation

```bash
# Run comprehensive evaluation suite
python scripts/evaluate_agent.py

# Generates:
# - evaluation_report_YYYYMMDD_HHMMSS.md   (Markdown)
# - evaluation_report_YYYYMMDD_HHMMSS.json (Structured data)
# - evaluation_report_YYYYMMDD_HHMMSS.tex  (LaTeX for PDF)
```

### Evaluation Report Generator (`scripts/evaluation_report.py`)

Generates paper-style evaluation reports with:

#### Metrics Implemented

| Metric | Purpose | Formula |
|--------|---------|---------|
| **Triage Recall** | Emergency/urgent detection coverage | TP / (TP + FN) |
| **Triage Precision** | False positive rate | TP / (TP + FP) |
| **F1-Score** | Harmonic mean of precision/recall | 2×(P×R)/(P+R) |
| **Specificity** | True negative rate | TN / (TN + FP) |
| **Approval Rate** | % responses approved without escalation | Approved / Total |
| **Escalation Rate** | % requiring human review | Escalated / Total |
| **Response Latency** | Computational efficiency | Mean, Median, P95, P99 |
| **Reflection Iterations** | System-2 thinking cost | Mean iterations/response |
| **Hallucination Detection** | Claims without evidence | Detected / Total |
| **Contraindication Catch Rate** | Drug interaction safety | Caught / Total |

#### Benchmark Datasets

**MedQA Benchmark** (5 representative cases):
- Emergency: Chest pain + shortness of breath (ACS)
- Emergency: Acute abdomen with peritonitis signs
- Urgent: High fever + throat pain (pharyngitis)
- Routine: Mild headache (3 days)
- Routine: Mild cough (no fever)

**Safety Test Cases** (5 adversarial cases):
- NSAID + diabetes (kidney risk)
- Abrupt diabetes med discontinuation
- Aspirin allergy + ibuprofen cross-reactivity
- Warfarin + vitamin K antagonism
- Normal vitals (no safety concern)

**Hallucination Test Cases** (3 non-existent conditions):
- "Fictitious Syndrome Z"
- "Imaginex" drug
- "BloodHarmony Panel" test

#### Report Formats

1. **Markdown** (`*.md`)
   - Human-readable tables and sections
   - Includes benchmark case details
   - Methodology explanation
   - Ready for documentation

2. **JSON** (`*.json`)
   - Structured metric data
   - Programmatic parsing
   - Integration with CI/CD pipelines
   - Time-series tracking

3. **LaTeX** (`*.tex`)
   - PDF generation: `pdflatex evaluation_report.tex`
   - Publication-ready formatting
   - Mathematical notation support
   - Compliant with paper submission standards

### Usage Example

```python
from scripts.evaluation_report import EvaluationReport
from src.config import Settings

# Initialize report generator
settings = Settings()
report = EvaluationReport(settings, results_dir="results")

# Add results from workflow execution
report.add_triage_result(
    predicted=TriageLevel.EMERGENCY,
    expected=TriageLevel.EMERGENCY
)

report.add_safety_result(
    is_approved=True,
    has_contraindication=False,
    has_hallucination=False,
    has_error=False
)

report.add_performance_data(
    response_time_ms=1234.5,
    reflection_iterations=2,
    token_usage=450
)

# Generate and save all reports
paths = report.save_reports()
# → {
#     'markdown': Path('results/evaluation_report_20260215_123456.md'),
#     'json': Path('results/evaluation_report_20260215_123456.json'),
#     'latex': Path('results/evaluation_report_20260215_123456.tex')
#   }
```

---

## 🔄 Real Data ETL Pipelines

### Quick Start: Data Ingestion

```python
from scripts.data_ingestion_etl import MedQuADETL, SyntheaETL, PDFDocumentETL
from src.config import Settings

settings = Settings()

# 1. MedQuAD (Medical Q&A)
medquad_pipeline = MedQuADETL(settings)
documents = medquad_pipeline.ingest_medquad("data/medquad")

# 2. Synthea (Synthetic EHR)
synthea_pipeline = SyntheaETL(settings)
count, errors = synthea_pipeline.ingest_synthea("data/synthea_output")

# 3. PDF Documents (Guidelines, Literature)
pdf_pipeline = PDFDocumentETL(settings)
documents = pdf_pipeline.ingest_pdf_documents("data/docs", vector_store)
```

### ETL Pipeline Components

#### MedQuAD ETL (`MedQuADETL`)

**Source**: https://github.com/abachaa/MedQuAD

**Data Format**: XML Q&A pairs from medical institutions
- GARD: Genetic and Rare Diseases
- NCCIH: Complementary & Integrative Health
- NHLBI: Heart, Lung, Blood Institute
- NCI: Cancer Institute
- NINDS: Neurological Disorders
- PlainLanguage: Accessible health information
- RareDiseases: Additional rare disease content

**Usage**:
```bash
# Download MedQuAD dataset
git clone https://github.com/abachaa/MedQuAD data/medquad

# Ingest into Qdrant vector database
python -c "
from scripts.data_ingestion_etl import MedQuADETL
from src.config import Settings

pipeline = MedQuADETL(Settings())
docs = pipeline.ingest_medquad('data/medquad')
print(f'Ingested {len(docs)} Q&A pairs')
"
```

**Output**: Documents with fields:
- `question`: User query
- `answer`: Authoritative response
- `category`: Source institution
- `content`: Combined Q&A text
- `metadata`: Content hash, ingest date, source file

---

#### Synthea ETL (`SyntheaETL`)

**Source**: https://github.com/synthetichealth/synthea

**Data Format**: Realistic synthetic EHR data in CSV format
- `patients.csv`: Demographics, vitals (age, gender, address, phone, email)
- `encounters.csv`: Clinical visits (timestamp, type, provider, location)
- `conditions.csv`: ICD-10 diagnoses (code, description, onset date)
- `medications.csv`: Prescriptions (RxNorm code, start/end dates)
- `allergies.csv`: Documented allergies (allergen, reaction, severity)

**Installation & Setup**:
```bash
# 1. Clone Synthea repository
git clone https://github.com/synthetichealth/synthea
cd synthea

# 2. Generate synthetic patients (default: 100 patients)
./run_synthea.sh -p 100

# 3. Output location:
# synthea/output/csv/
#   ├── patients.csv
#   ├── encounters.csv
#   ├── conditions.csv
#   ├── medications.csv
#   └── allergies.csv

# 4. Copy to neuro-triage data directory
cp -r output/csv ../neuro-triage/data/synthea_output/
```

**Usage**:
```bash
# Ingest Synthea data into PostgreSQL
python -c "
from scripts.data_ingestion_etl import SyntheaETL
from src.config import Settings

pipeline = SyntheaETL(Settings())
count, errors = pipeline.ingest_synthea('data/synthea_output')
print(f'Loaded {count} records with {errors} errors')
"
```

**Output**: Database tables populated:
- `patients`: 100 realistic synthetic patients
- `medical_records`: Conditions + ICD-10 codes
- `medications`: Active prescriptions
- `allergies`: Known allergies + severities

**Benefits for Neuro-Triage**:
- ✅ Realistic patient histories vs. synthetic data
- ✅ Diverse demographics and conditions
- ✅ Proper medication/allergy relationships
- ✅ Encounter timestamps for temporal analysis
- ✅ ICD-10 standardization for interoperability

---

#### PDF Document ETL (`PDFDocumentETL`)

**Data Format**: Medical literature, guidelines, policy documents
- Clinical practice guidelines (AHA, ACC, AMA)
- Research papers (PubMed, arXiv)
- Hospital policies and procedures
- Training materials and standards

**Installation**:
```bash
pip install PyPDF2
```

**Usage**:
```bash
# Create document directory structure
mkdir -p data/docs/{guidelines,literature,policies,training}

# Add PDF files to appropriate subdirectories
cp clinical_guidelines.pdf data/docs/guidelines/
cp research_papers.pdf data/docs/literature/
cp hospital_policy.pdf data/docs/policies/

# Ingest into Qdrant
python -c "
from scripts.data_ingestion_etl import PDFDocumentETL
from src.config import Settings

pipeline = PDFDocumentETL(Settings())
docs = pipeline.ingest_pdf_documents('data/docs', vector_store=None)
print(f'Ingested {len(docs)} document chunks')
"
```

**Processing**:
- Extracts text from all PDFs recursively
- Chunks text into 1000-char segments with 100-char overlap
- Computes content hash for deduplication
- Stores metadata: file path, page count, chunk number, ingest date

**Output**: Documents with fields:
- `source`: "PDF"
- `file`: Filename
- `category`: Subdirectory (guidelines, literature, etc.)
- `content`: Text chunk
- `metadata`: Content hash, page count, chunk index, ingest date

---

#### Generic CSV ETL (`CSVDatasetETL`)

**Purpose**: Load any CSV-formatted clinical data with flexible field mapping

**Usage**:
```python
from scripts.data_ingestion_etl import CSVDatasetETL
from src.database.models import Patient
from src.config import Settings

pipeline = CSVDatasetETL(Settings())

# Define field mapping (CSV column → model field)
mapping = {
    "PatientID": "id",
    "FirstName": "first_name",
    "LastName": "last_name",
    "DOB": "date_of_birth",
    "Gender": "gender",
    "Address": "address",
    "Phone": "phone",
    "Email": "email"
}

# Load CSV into database
count, errors = pipeline.ingest_csv_dataset(
    csv_file="data/patients.csv",
    model_class=Patient,
    field_mapping=mapping
)

print(f"Loaded {count} records with {errors} errors")
```

**Features**:
- Automatic type conversion (strings → dates, floats, etc.)
- NULL/NaN handling
- Null value filtering (skips empty fields)
- Error resilience (continues on individual row failures)
- Flexible field mapping (any CSV → any model)

---

## 🎯 Full Data Integration Workflow

### Step 1: Set Up Data Directories

```bash
# Create data directory structure
mkdir -p data/{medquad,synthea_output,docs/{guidelines,literature,policies}}

# Download real datasets
git clone https://github.com/abachaa/MedQuAD data/medquad
git clone https://github.com/synthetichealth/synthea
cd synthea && ./run_synthea.sh -p 100 && cd ..
cp synthea/output/csv data/synthea_output/
```

### Step 2: Run ETL Pipelines

```python
# scripts/ingest_all_data.py
import logging
from src.config import Settings
from scripts.data_ingestion_etl import (
    MedQuADETL,
    SyntheaETL,
    PDFDocumentETL,
    CSVDatasetETL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()

logger.info("=" * 70)
logger.info("PHASE 7: REAL DATA INGESTION")
logger.info("=" * 70)

# 1. MedQuAD
logger.info("\n[1] Ingesting MedQuAD...")
medquad = MedQuADETL(settings)
medquad_docs = medquad.ingest_medquad("data/medquad")
logger.info(f"✓ {len(medquad_docs)} MedQuAD documents ingested")

# 2. Synthea
logger.info("\n[2] Ingesting Synthea EHR data...")
synthea = SyntheaETL(settings)
synthea_count, synthea_errors = synthea.ingest_synthea("data/synthea_output")
logger.info(f"✓ {synthea_count} Synthea records ingested ({synthea_errors} errors)")

# 3. PDF Documents
logger.info("\n[3] Ingesting PDF documents...")
pdf = PDFDocumentETL(settings)
pdf_docs = pdf.ingest_pdf_documents("data/docs", vector_store=None)
logger.info(f"✓ {len(pdf_docs)} PDF chunks ingested")

logger.info("\n" + "=" * 70)
logger.info("DATA INGESTION COMPLETE")
logger.info("=" * 70)
```

### Step 3: Run Evaluation

```bash
# Run evaluation against ingested data
python scripts/evaluate_agent.py

# Generate reports
# - evaluation_report_YYYYMMDD_HHMMSS.md
# - evaluation_report_YYYYMMDD_HHMMSS.json
# - evaluation_report_YYYYMMDD_HHMMSS.tex
```

---

## 📈 Metrics & Analysis

### Triage Metrics Example Output

```
### Triage Classification Metrics
  Recall (Sensitivity): 96.0%          (catches 96% of true emergencies)
  Precision:            92.0%          (8% false alarms)
  F1-Score:             0.941          (balanced metric)
  Specificity:          98.0%          (correctly identifies 98% of non-emergencies)
```

### Safety Metrics Example Output

```
### Safety & Approval Metrics
  Total Queries:        13
  Approved:             10 (76.9%)     (auto-approved without escalation)
  Escalated:            3 (23.1%)      (flagged for human review)
  Errors:               0 (0.0%)       (system stability)
  Contraindications Caught: 3          (drug interaction detection)
  Hallucinations Detected:  0          (factuality maintenance)
```

### Performance Metrics Example Output

```
### Performance & Latency (milliseconds)
  Mean Latency:         1234.5ms       (average response time)
  Median Latency:       1150.0ms       (typical user experience)
  P95 Latency:          2100.5ms       (95% of requests faster)
  P99 Latency:          2850.0ms       (99% of requests faster)
  Mean Reflection Iter: 1.85           (avg System-2 thinking iterations)
```

---

## 🔧 Troubleshooting

### Common Issues

**MedQuAD ingestion is slow**
- Expected for full dataset (>100k Q&A pairs)
- Use `max(100)` for testing; full dataset for production
- Consider parallel processing with `ThreadPoolExecutor`

**Synthea CSV not found**
```bash
# Verify directory structure
ls -la data/synthea_output/
# Should show: patients.csv, conditions.csv, medications.csv, allergies.csv, encounters.csv
```

**PDF text extraction fails**
```bash
pip install --upgrade PyPDF2
# Try alternative: install pdfplumber or pypdf
```

**Database constraint violations**
- Ensure foreign keys are populated in correct order
- Load patients before medical records/medications
- Check for NULL values in required fields

---

## 📚 References

- **MedQuAD**: https://github.com/abachaa/MedQuAD
- **Synthea**: https://github.com/synthetichealth/synthea
- **Medical Data Standards**: HL7 FHIR, ICD-10, RxNorm
- **Evaluation Framework**: Paper appendix, metrics definitions

