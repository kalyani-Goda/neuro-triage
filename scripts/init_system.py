"""Initialization and setup script."""

import logging
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required packages are installed."""
    logger.info("Checking dependencies...")
    
    required_packages = [
        "langchain",
        "langgraph",
        "qdrant_client",
        "psycopg2",
        "redis",
        "fastapi",
        "streamlit",
        "presidio_analyzer",
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"Missing packages: {missing}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✓ All dependencies installed")
    return True


def check_environment():
    """Check environment variables."""
    logger.info("Checking environment variables...")
    
    required_vars = ["OPENAI_API_KEY"]
    missing = []
    
    for var in required_vars:
        if not __import__("os").getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"Missing environment variables: {missing}")
        logger.warning("Create .env file with required variables")
        return False
    
    logger.info("✓ Environment variables configured")
    return True


def init_databases():
    """Initialize databases."""
    logger.info("Initializing databases...")
    
    try:
        from src.infrastructure.database import init_db
        init_db()
        logger.info("✓ PostgreSQL initialized")
        
        from src.infrastructure.qdrant_manager import qdrant_manager
        qdrant_manager.initialize_collection()
        logger.info("✓ Qdrant collection initialized")
        
        from src.infrastructure.redis_manager import redis_manager
        if redis_manager.health_check():
            logger.info("✓ Redis connected")
        else:
            logger.warning("⚠ Redis health check failed")
            
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def load_sample_data():
    """Load sample data."""
    logger.info("Loading sample data...")
    
    try:
        from src.infrastructure.etl_patients import PatientETL
        PatientETL.load_synthetic_patients(count=20)
        logger.info("✓ Sample patients loaded")
        
        from src.infrastructure.ingest_docs import MedicalKnowledgeIngester
        MedicalKnowledgeIngester.ingest_sample_documents()
        logger.info("✓ Medical knowledge ingested")
        
        return True
    except Exception as e:
        logger.error(f"Sample data loading failed: {e}")
        return False


def main():
    """Run initialization."""
    logger.info("=" * 60)
    logger.info("Neuro-Triage System Initialization")
    logger.info("=" * 60)
    
    steps = [
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Databases", init_databases),
        ("Sample Data", load_sample_data),
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        logger.info(f"\\n[{step_name}]")
        try:
            if not step_func():
                all_passed = False
                logger.warning(f"✗ {step_name} initialization incomplete")
        except Exception as e:
            logger.error(f"✗ {step_name} failed: {e}")
            all_passed = False
    
    logger.info("\\n" + "=" * 60)
    if all_passed:
        logger.info("✓ System initialization complete!")
        logger.info("\\nNext steps:")
        logger.info("1. Start backend: python -m src.api.main")
        logger.info("2. Start frontend: streamlit run src/ui/app.py")
        logger.info("3. Visit: http://localhost:8501")
    else:
        logger.error("✗ Some initialization steps failed")
        logger.error("Check logs above and fix issues")
        sys.exit(1)
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
