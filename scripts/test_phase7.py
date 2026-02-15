#!/usr/bin/env python3
"""Quick verification of PHASE 7 modules."""

from scripts.data_ingestion_etl import MedQuADETL, SyntheaETL, PDFDocumentETL, CSVDatasetETL
from scripts.evaluation_report import EvaluationReport
from src.config import Settings

settings = Settings()

print('✅ All PHASE 7 modules loaded successfully!')
print()
print('Available Components:')
print('  1. Evaluation Report System')
report = EvaluationReport(settings)
print(f'     - {len(report.MEDQA_BENCHMARK)} MedQA benchmark cases')
print(f'     - {len(report.SAFETY_TEST_CASES)} safety test cases')
print(f'     - {len(report.HALLUCINATION_TEST_CASES)} hallucination tests')
print()
print('  2. ETL Pipelines')
medquad = MedQuADETL(settings)
synthea = SyntheaETL(settings)
pdf = PDFDocumentETL(settings)
csv = CSVDatasetETL(settings)
print('     - MedQuADETL (Medical Q&A dataset)')
print('     - SyntheaETL (Synthetic EHR data)')
print('     - PDFDocumentETL (Medical documents)')
print('     - CSVDatasetETL (Generic CSV data)')
print()
print('✅ PHASE 7 Ready!')
