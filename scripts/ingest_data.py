#!/usr/bin/env python3
"""
PHASE 7: Simple Data Ingestion Script
Run this to ingest real datasets into your database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def ingest_medquad():
    """Ingest MedQuAD dataset."""
    logger.info("\n" + "="*70)
    logger.info("INGESTING MEDQUAD DATASET")
    logger.info("="*70)
    
    medquad_path = Path("data/medquad")
    
    if not medquad_path.exists():
        logger.warning(f"\n⚠️  MedQuAD not found at: {medquad_path}")
        logger.info("To download MedQuAD:")
        logger.info("  git clone https://github.com/abachaa/MedQuAD data/medquad")
        logger.info("  Then run this script again")
        return False
    
    try:
        from scripts.data_ingestion_etl import MedQuADETL
        from src.config import Settings
        
        settings = Settings()
        pipeline = MedQuADETL(settings)
        documents = pipeline.ingest_medquad(str(medquad_path))
        
        logger.info(f"✅ Successfully ingested {len(documents)} MedQuAD documents")
        logger.info(f"   Summary: {pipeline.log_summary()}")
        
        # Note: MedQuAD documents are parsed and ready for retrieval
        # Vector embedding happens on-demand during retrieval via embedding service
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MedQuAD ingestion failed: {e}")
        return False


def ingest_synthea():
    """Ingest Synthea EHR data."""
    logger.info("\n" + "="*70)
    logger.info("INGESTING SYNTHEA EHR DATA")
    logger.info("="*70)
    
    synthea_path = Path("data/synthea_output")
    
    if not synthea_path.exists():
        logger.warning(f"\n⚠️  Synthea output not found at: {synthea_path}")
        logger.info("To generate Synthea data:")
        logger.info("  1. git clone https://github.com/synthetichealth/synthea")
        logger.info("  2. cd synthea && ./run_synthea.sh -p 100")
        logger.info("  3. cp -r output/csv ../neuro-triage/data/synthea_output/")
        logger.info("  Then run this script again")
        return False
    
    try:
        from scripts.data_ingestion_etl import SyntheaETL
        from src.config import Settings
        
        settings = Settings()
        pipeline = SyntheaETL(settings)
        count, errors = pipeline.ingest_synthea(str(synthea_path))
        
        logger.info(f"✅ Successfully ingested {count} Synthea records")
        logger.info(f"   Errors: {errors}")
        logger.info(f"   Summary: {pipeline.log_summary()}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Synthea ingestion failed: {e}")
        return False


def ingest_pdfs():
    """Ingest PDF documents."""
    logger.info("\n" + "="*70)
    logger.info("INGESTING PDF DOCUMENTS")
    logger.info("="*70)
    
    docs_path = Path("data/docs")
    
    if not docs_path.exists():
        logger.warning(f"\n⚠️  Docs directory not found at: {docs_path}")
        logger.info("To add PDF documents:")
        logger.info("  1. mkdir -p data/docs/{guidelines,literature,policies}")
        logger.info("  2. cp your_medical_pdfs.pdf data/docs/guidelines/")
        logger.info("  Then run this script again")
        return False
    
    # Check if there are any PDF files
    pdfs = list(docs_path.rglob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in data/docs/")
        return False
    
    try:
        from scripts.data_ingestion_etl import PDFDocumentETL
        from src.config import Settings
        
        settings = Settings()
        pipeline = PDFDocumentETL(settings)
        documents = pipeline.ingest_pdf_documents(str(docs_path), vector_store=None)
        
        logger.info(f"✅ Successfully ingested {len(documents)} PDF document chunks")
        logger.info(f"   Summary: {pipeline.log_summary()}")
        return True
        
    except Exception as e:
        logger.error(f"❌ PDF ingestion failed: {e}")
        return False


def main():
    """Run all available ingestion pipelines."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 7: REAL DATA INGESTION")
    logger.info("="*80)
    
    results = {}
    
    # MedQuAD (if available)
    results["medquad"] = ingest_medquad()
    
    # Synthea (if available)
    results["synthea"] = ingest_synthea()
    
    # PDFs (if available)
    results["pdfs"] = ingest_pdfs()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("INGESTION SUMMARY")
    logger.info("="*80)
    
    for dataset, success in results.items():
        status = "✅ SUCCESS" if success else "⏭️  SKIPPED"
        logger.info(f"{status}: {dataset.upper()}")
    
    completed = sum(1 for v in results.values() if v)
    logger.info(f"\nCompleted: {completed}/{len(results)} datasets")
    
    if completed == 0:
        logger.info("\n💡 To ingest real data:")
        logger.info("   1. Download MedQuAD: git clone https://github.com/abachaa/MedQuAD data/medquad")
        logger.info("   2. Generate Synthea: https://github.com/synthetichealth/synthea")
        logger.info("   3. Add PDFs to: data/docs/")
        logger.info("   4. Run this script again")
        return 1
    
    logger.info("\n✅ Data ingestion complete!")
    logger.info("   Now run: python scripts/run_evaluation.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
