"""Medical knowledge document ingestion."""

import logging
from typing import List, Dict, Any
import json
from pathlib import Path

from src.infrastructure.qdrant_manager import qdrant_manager
from src.agent.tools import embedding_manager

logger = logging.getLogger(__name__)


class MedicalKnowledgeIngester:
    """Ingest medical knowledge documents into vector database."""

    # Sample medical knowledge (in production, these would be from MedQuAD, PDFs, etc.)
    SAMPLE_DOCUMENTS = [
        {
            "title": "Hypertension Management",
            "content": "Hypertension is defined as systolic BP ≥130 mmHg or diastolic BP ≥80 mmHg. First-line treatments include ACE inhibitors, ARBs, calcium channel blockers, and thiazide diuretics.",
            "source": "Clinical Guidelines",
            "category": "Cardiovascular",
        },
        {
            "title": "Diabetes Type 2 Management",
            "content": "Type 2 diabetes management includes lifestyle modification, metformin as first-line medication, and additional agents if needed (GLP-1 agonists, sulfonylureas).",
            "source": "Clinical Guidelines",
            "category": "Endocrinology",
        },
        {
            "title": "Chest Pain Emergency Assessment",
            "content": "Chest pain is an emergency symptom requiring immediate evaluation. Possible causes include acute MI, PE, aortic dissection, pneumothorax. Immediate EKG, troponin, and imaging indicated.",
            "source": "Emergency Guidelines",
            "category": "Emergency",
        },
        {
            "title": "Drug Interaction: NSAIDs and ACE Inhibitors",
            "content": "Concurrent use of NSAIDs and ACE inhibitors increases risk of acute renal failure, especially in elderly and dehydrated patients. Avoid or monitor closely.",
            "source": "Drug Database",
            "category": "Drug Interactions",
        },
        {
            "title": "Asthma Exacerbation Treatment",
            "content": "Acute asthma exacerbation treatment includes beta-2 agonists (albuterol), corticosteroids, and oxygen. Severe cases may require IV magnesium or ICU admission.",
            "source": "Respiratory Guidelines",
            "category": "Respiratory",
        },
        {
            "title": "Sepsis Recognition and Treatment",
            "content": "Sepsis is a medical emergency with high mortality. Early recognition using qSOFA criteria, prompt antibiotics within 1 hour, and supportive care are critical.",
            "source": "ICU Guidelines",
            "category": "Emergency",
        },
        {
            "title": "Stroke Assessment (NIHSS)",
            "content": "Acute stroke is a medical emergency. Time-sensitive interventions include thrombolytics (within 4.5 hours) and mechanical thrombectomy (within 24 hours). Rapid assessment essential.",
            "source": "Neurology Guidelines",
            "category": "Emergency",
        },
        {
            "title": "Penicillin Allergy Assessment",
            "content": "True penicillin allergy (IgE-mediated) is rare (~1%). Delayed rashes are common but not true allergy. Cross-reactivity with cephalosporins is <3% for 3rd gen. Allergy testing can clarify.",
            "source": "Allergy Guidelines",
            "category": "Allergies",
        },
    ]

    @staticmethod
    def ingest_sample_documents() -> int:
        """Ingest sample documents into Qdrant."""
        logger.info("Ingesting sample medical knowledge...")

        try:
            # Initialize Qdrant collection
            qdrant_manager.initialize_collection()

            # Embed and ingest documents
            documents = []
            embeddings = []

            for doc in MedicalKnowledgeIngester.SAMPLE_DOCUMENTS:
                # Create searchable content
                full_text = f"{doc['title']}. {doc['content']}"

                # Embed the document
                embedding = embedding_manager.embed_text(full_text)
                if not embedding:
                    logger.warning(f"Failed to embed: {doc['title']}")
                    continue

                documents.append({
                    "title": doc["title"],
                    "content": doc["content"],
                    "source": doc["source"],
                    "category": doc["category"],
                })

                embeddings.append(embedding)

            # Add to Qdrant
            if documents and embeddings:
                success = qdrant_manager.add_documents(documents, embeddings)
                if success:
                    logger.info(f"Ingested {len(documents)} documents successfully")
                    return len(documents)

        except Exception as e:
            logger.error(f"Ingestion error: {e}")

        return 0

    @staticmethod
    def ingest_from_file(file_path: str) -> int:
        """Ingest documents from a JSON file."""
        logger.info(f"Ingesting from file: {file_path}")

        try:
            with open(file_path, "r") as f:
                documents = json.load(f)

            if not isinstance(documents, list):
                documents = [documents]

            qdrant_manager.initialize_collection()

            ingested = 0
            embeddings_list = []
            docs_list = []

            for doc in documents:
                full_text = f"{doc.get('title', '')}. {doc.get('content', '')}"

                embedding = embedding_manager.embed_text(full_text)
                if not embedding:
                    continue

                embeddings_list.append(embedding)
                docs_list.append(doc)
                ingested += 1

            if embeddings_list and docs_list:
                qdrant_manager.add_documents(docs_list, embeddings_list)

            logger.info(f"Ingested {ingested} documents from file")
            return ingested

        except Exception as e:
            logger.error(f"File ingestion error: {e}")
            return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    MedicalKnowledgeIngester.ingest_sample_documents()
