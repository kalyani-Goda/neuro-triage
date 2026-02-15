#!/usr/bin/env python3
"""
PHASE 7: Quick-Start Script for Evaluation & Real Data Ingestion
Run this to execute the full evaluation pipeline
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with error handling."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"$ {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    return True

def main():
    """Execute evaluation pipeline."""
    print("\n" + "="*70)
    print("NEURO-TRIAGE: PHASE 7 EVALUATION & DATA INGESTION")
    print("="*70)
    
    # Check if running in conda environment
    print("\nChecking environment...")
    env_check = subprocess.run(
        "conda run -n neuro-triage python --version",
        shell=True,
        capture_output=True
    )
    if env_check.returncode != 0:
        print("❌ Conda environment 'neuro-triage' not found")
        print("   Run: conda create -n neuro-triage python=3.11")
        sys.exit(1)
    print("✅ Environment: neuro-triage conda environment found")
    
    # Verify Docker services
    print("\nVerifying Docker services...")
    docker_check = subprocess.run(
        "docker ps | grep neuro-triage",
        shell=True,
        capture_output=True
    )
    if docker_check.returncode != 0:
        print("⚠️  Docker services not running")
        print("   Start with: docker-compose up -d")
        print("   Continuing with evaluation (may skip database tests)...\n")
    else:
        print("✅ Docker services running")
    
    # Phase 1: Run Tests
    success = run_command(
        "conda run -n neuro-triage python -m pytest tests/ -v",
        "PHASE 7.1: Running Unit Tests"
    )
    if not success:
        print("\n⚠️  Some tests failed. Review output above.")
    
    # Phase 2: Run Evaluation
    success = run_command(
        "conda run -n neuro-triage python scripts/evaluate_agent.py",
        "PHASE 7.2: Running Comprehensive Evaluation"
    )
    if success:
        print("\n✅ Evaluation complete!")
        print("   Reports generated in: results/")
    else:
        print("\n❌ Evaluation failed")
        sys.exit(1)
    
    # Phase 3: Display Results
    results_dir = Path("results")
    if results_dir.exists():
        print("\n" + "="*70)
        print("GENERATED REPORTS")
        print("="*70)
        
        reports = list(results_dir.glob("evaluation_report_*.md"))
        if reports:
            latest = sorted(reports)[-1]
            print(f"\n📄 Latest Report: {latest.name}")
            print("\nPreview (first 50 lines):")
            print("-"*70)
            with open(latest) as f:
                lines = f.readlines()[:50]
                print("".join(lines))
            print("-"*70)
        
        json_reports = list(results_dir.glob("evaluation_report_*.json"))
        if json_reports:
            latest_json = sorted(json_reports)[-1]
            print(f"\n📊 JSON Report: {latest_json.name}")
            print(f"   Path: {latest_json.absolute()}")
        
        tex_reports = list(results_dir.glob("evaluation_report_*.tex"))
        if tex_reports:
            latest_tex = sorted(tex_reports)[-1]
            print(f"\n📋 LaTeX Report: {latest_tex.name}")
            print(f"   Path: {latest_tex.absolute()}")
            print(f"   To generate PDF: pdflatex {latest_tex.name}")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Review evaluation reports in results/ directory:
   - evaluation_report_*.md  (human-readable)
   - evaluation_report_*.json (programmatic)
   - evaluation_report_*.tex  (PDF generation)

2. Integrate real data (optional):
   - Download MedQuAD: https://github.com/abachaa/MedQuAD
   - Generate Synthea: https://github.com/synthetichealth/synthea
   - Run: python scripts/data_ingestion_etl.py

3. For detailed ETL documentation:
   - See: scripts/EVALUATION_ETL_README.md

4. For more evaluation options:
   - Run: python scripts/evaluate_agent.py --help
   - Modify benchmark datasets in scripts/evaluation_report.py

5. Launch Streamlit UI:
   - streamlit run src/ui/app.py
   
6. Start API server:
   - python -m src.api.main
""")
    print("="*70)

if __name__ == "__main__":
    main()
