# PHASE 7: Data Ingestion Quick Reference

## 📊 Current Status

### ✅ What Exists
- **ETL Scripts**: Ready in `scripts/data_ingestion_etl.py`
- **Evaluation System**: Ready with 13 benchmark cases
- **Database**: PostgreSQL with 7 tables initialized

### 📦 Database Content (Current)
```
Database: neuro_triage (PostgreSQL)

patients:              100 synthetic records
patient_medical_history: 200 synthetic records
medications:           110 synthetic records
allergies:             Populated
consultation_sessions: Ready
conversation_logs:     Ready
audit_logs:           Ready
```

### ❌ Missing
- MedQuAD Q&A pairs (0 ingested)
- Synthea realistic EHR (0 ingested)
- PDF documents (0 ingested)

---

## 🚀 How to Ingest Real Data

### Quick Option: Run Ingestion Script
```bash
# This will attempt to ingest ANY available datasets
python scripts/ingest_data.py

# It will tell you what's missing and how to get it
```

### Step-by-Step: MedQuAD Only (Simplest)

```bash
# 1. Download MedQuAD (one-time, ~2GB)
git clone https://github.com/abachaa/MedQuAD data/medquad

# 2. Ingest into database
conda run -n neuro-triage python scripts/ingest_data.py

# 3. Verify
docker exec neuro-triage-postgres psql -U neuro_user -d neuro_triage \
  -c "SELECT COUNT(*) FROM document_embeddings;" 2>/dev/null || echo "Not in database yet"
```

### Full Integration: All Datasets (Comprehensive)

```bash
# MedQuAD (100k+ medical Q&A)
git clone https://github.com/abachaa/MedQuAD data/medquad

# Synthea (realistic EHR data)
git clone https://github.com/synthetichealth/synthea
cd synthea
./run_synthea.sh -p 100  # Generate 100 patients
cd ..
cp -r synthea/output/csv data/synthea_output/

# PDFs (optional - add clinical guidelines)
mkdir -p data/docs/{guidelines,literature}
# Copy your PDF files here

# Ingest all
conda run -n neuro-triage python scripts/ingest_data.py
```

---

## 📋 ETL Pipelines Available

### 1. MedQuADETL
- **Source**: XML files with medical Q&A pairs
- **Capacity**: 100,000+ pairs
- **Output**: Documents ready for vector search
- **Time**: ~5-10 min for full dataset

```python
from scripts.data_ingestion_etl import MedQuADETL
from src.config import Settings

pipeline = MedQuADETL(Settings())
docs = pipeline.ingest_medquad("data/medquad")
print(f"Ingested {len(docs)} documents")
```

### 2. SyntheaETL
- **Source**: CSV files (patients, conditions, meds, allergies)
- **Capacity**: Scalable (10 to 100k+ patients)
- **Output**: PostgreSQL tables
- **Time**: ~2-5 min depending on patient count

```python
from scripts.data_ingestion_etl import SyntheaETL
from src.config import Settings

pipeline = SyntheaETL(Settings())
count, errors = pipeline.ingest_synthea("data/synthea_output")
print(f"Loaded {count} records, {errors} errors")
```

### 3. PDFDocumentETL
- **Source**: Any PDF files
- **Processing**: Text extraction + smart chunking
- **Output**: Qdrant-ready chunks
- **Time**: ~1-2 min for 10-20 PDFs

```python
from scripts.data_ingestion_etl import PDFDocumentETL
from src.config import Settings

pipeline = PDFDocumentETL(Settings())
docs = pipeline.ingest_pdf_documents("data/docs", vector_store=None)
print(f"Ingested {len(docs)} document chunks")
```

### 4. CSVDatasetETL
- **Source**: Any CSV file with defined schema
- **Usage**: Generic loader for vendor data
- **Output**: SQLAlchemy model tables

```python
from scripts.data_ingestion_etl import CSVDatasetETL
from src.memory.models import Patient
from src.config import Settings

pipeline = CSVDatasetETL(Settings())
mapping = {"PatientID": "patient_id", "FirstName": "first_name"}
count, errors = pipeline.ingest_csv_dataset("data/patients.csv", Patient, mapping)
```

---

## 🔍 Verify Data Ingestion

### Check Database Records
```bash
# Count synthetic patients
docker exec neuro-triage-postgres psql -U neuro_user -d neuro_triage \
  -c "SELECT COUNT(*) as total_patients FROM patients;"

# Expected: 100 (synthetic)

# After ingestion - check if Synthea added more
# Expected: 100 + number_of_synthea_patients
```

### Check Qdrant Vector Store
```bash
# Verify Qdrant is running
curl http://localhost:6333/health

# Check collections (requires curl + jq)
curl http://localhost:6333/collections | jq .
```

---

## 🎯 Decision: Synthetic vs Real Data

### Use **Synthetic Data** (Current) If:
- ✅ You want to test evaluation system quickly
- ✅ You don't have time to download datasets
- ✅ You're developing/debugging
- ⏱️ Time: < 1 minute to start evaluation

**Command**:
```bash
python scripts/run_evaluation.py
```

### Use **Real Data** (Recommended) If:
- ✅ You want realistic metrics
- ✅ You're preparing for production
- ✅ You need to demonstrate with real medical knowledge
- ✅ You're publishing results
- ⏱️ Time: 10-30 minutes to download + ingest

**Command**:
```bash
# Download
git clone https://github.com/abachaa/MedQuAD data/medquad

# Ingest
python scripts/ingest_data.py

# Evaluate
python scripts/run_evaluation.py
```

---

## 📝 Common Questions

**Q: How much disk space for real data?**
- MedQuAD: ~2GB
- Synthea (100 patients): ~50MB
- PDFs: Depends on your collection
- Total: ~2.5-3GB

**Q: Will ingestion overwrite synthetic data?**
- No, it appends. Your synthetic patients stay + real data is added
- Total records: 100 synthetic + whatever you ingest

**Q: Can I ingest just MedQuAD without Synthea?**
- Yes! Each pipeline is independent
- Run `python scripts/ingest_data.py` and it will ingest whatever's available

**Q: How long does ingestion take?**
- MedQuAD: 5-10 minutes (100k+ files)
- Synthea: 2-5 minutes (depends on patient count)
- PDFs: 1-2 minutes (depends on doc count)

**Q: What happens if ingestion fails?**
- Pipeline logs errors and continues
- Run again - it will skip already-ingested data (via content hash)
- Check logs for specific failures

---

## 🚦 Next Steps

### Option 1: Test with Synthetic (Fastest)
```bash
python scripts/run_evaluation.py
# Generates baseline metrics in ~2 minutes
```

### Option 2: Ingest MedQuAD (Recommended)
```bash
git clone https://github.com/abachaa/MedQuAD data/medquad
python scripts/ingest_data.py
python scripts/run_evaluation.py
```

### Option 3: Full Production Setup (Complete)
```bash
# All three datasets
# See "Full Integration" section above
python scripts/ingest_data.py
python scripts/run_evaluation.py
```

---

**Created**: February 15, 2026
**Status**: 🟢 Ready to ingest real data
**Scripts**: `scripts/ingest_data.py` and `scripts/data_ingestion_etl.py`
