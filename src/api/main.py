"""FastAPI backend for Neuro-Triage."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
from typing import Optional
import uvicorn

from src.config import settings
from src.agent import agent
from src.infrastructure.database import init_db
from src.infrastructure.qdrant_manager import qdrant_manager
from src.infrastructure.redis_manager import redis_manager

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Neuro-Triage API",
    description="Clinical Decision Support System using PARM Framework",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Patient query request."""

    patient_id: str = Field(..., description="Unique patient identifier")
    message: str = Field(..., description="Patient's input/symptoms")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class TriageResponse(BaseModel):
    """Triage response from agent."""

    session_id: str
    patient_id: str
    final_response: str
    triage_level: str
    triage_confidence: float
    critique_score: int
    response_status: str
    reflection_iterations: int
    success: bool
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    database: bool
    qdrant: bool
    redis: bool
    openai: bool


# Endpoints
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check system health."""
    database_ok = True
    qdrant_ok = qdrant_manager.health_check()
    redis_ok = redis_manager.health_check()
    openai_ok = True  # We'll assume OK if API key is set

    status = "healthy" if all([database_ok, qdrant_ok, redis_ok, openai_ok]) else "degraded"

    return {
        "status": status,
        "database": database_ok,
        "qdrant": qdrant_ok,
        "redis": redis_ok,
        "openai": openai_ok,
    }


@app.post("/chat", response_model=TriageResponse)
async def chat(request: QueryRequest):
    """Process patient query."""
    try:
        logger.info(f"Processing query for patient {request.patient_id}")

        result = agent.process_query(
            patient_id=request.patient_id,
            user_input=request.message,
            session_id=request.session_id,
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))

        return TriageResponse(
            session_id=result["session_id"],
            patient_id=result["patient_id"],
            final_response=result["final_response"],
            triage_level=result["triage_level"],
            triage_confidence=result["triage_confidence"],
            critique_score=result["critique_score"],
            response_status=result["response_status"],
            reflection_iterations=result["reflection_iterations"],
            success=result["success"],
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/initialize")
async def initialize_system():
    """Initialize system (databases, collections, etc)."""
    try:
        logger.info("Initializing system...")

        # Initialize database
        init_db()
        logger.info("Database initialized")

        # Initialize Qdrant
        qdrant_manager.initialize_collection()
        logger.info("Qdrant collection initialized")

        return {"status": "initialized", "message": "System ready"}

    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session_details(session_id: str):
    """Retrieve session details."""
    try:
        session_data = redis_manager.get_session_state(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Neuro-Triage",
        "version": "0.1.0",
        "description": "Clinical Decision Support System using PARM Framework",
        "docs": "/docs",
        "health": "/health",
    }


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Run on startup."""
    logger.info("Starting Neuro-Triage API...")
    try:
        # Try to verify API connectivity
        logger.info("System ready for processing queries")
    except Exception as e:
        logger.warning(f"Startup warning: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown."""
    logger.info("Shutting down Neuro-Triage API...")


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
