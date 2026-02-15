"""LLM tools for agent reasoning."""

import logging
from typing import Dict, Any, List, Tuple
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import settings
from src.infrastructure.qdrant_manager import qdrant_manager
from src.memory.patient_manager import PatientManager
from src.infrastructure.database import get_session

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manager for text embeddings."""

    def __init__(self):
        """Initialize embedding model."""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )

    def embed_text(self, text: str) -> List[float]:
        """Embed a text string."""
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []


class RetrievalTool:
    """Tool for retrieving medical knowledge from Qdrant."""

    def __init__(self):
        """Initialize retrieval tool."""
        self.embeddings = EmbeddingManager()

    def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant medical documents."""
        try:
            # Embed query
            query_vector = self.embeddings.embed_text(query)
            if not query_vector:
                logger.warning("Failed to embed query")
                return []

            # Search Qdrant
            documents = qdrant_manager.search(
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            logger.info(f"Retrieved {len(documents)} documents for query")
            return documents
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []


class PatientContextTool:
    """Tool for retrieving patient medical context."""

    def __init__(self):
        """Initialize patient context tool."""
        pass

    def get_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """Get complete patient medical context."""
        try:
            session = get_session()
            manager = PatientManager(session)
            
            patient_data = manager.get_patient(patient_id)
            session.close()
            
            if not patient_data:
                logger.warning(f"Patient not found: {patient_id}")
                return {"error": "Patient not found"}

            return patient_data
        except Exception as e:
            logger.error(f"Error retrieving patient context: {e}")
            return {"error": str(e)}


class LLMTool:
    """Base LLM tool for agent reasoning."""

    def __init__(self):
        """Initialize LLM."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.0,  # Deterministic for medical decisions
            api_key=settings.openai_api_key,
        )

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1000,
    ) -> Tuple[str, bool]:
        """Generate response from LLM."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]

            response = self.llm.invoke(messages)
            return response.content, False
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "", True


# Global tool instances
embedding_manager = EmbeddingManager()
retrieval_tool = RetrievalTool()
patient_context_tool = PatientContextTool()
llm_tool = LLMTool()
