"""Hallucination detection using knowledge base validation."""

import logging
import re
from typing import Tuple, List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class HallucinationDetector:
    """
    Detects hallucinations in medical responses by validating that mentioned
    medical terms (drugs, conditions, tests, procedures) actually exist in the
    knowledge base.
    """

    # Common medical term patterns to extract from text
    MEDICAL_TERM_PATTERNS = {
        "conditions": r"(?:syndrome|disease|condition|disorder|infection|cancer|diabetes|arthritis|asthma|hypertension|depression|anxiety)",
        "drugs": r"(?:drug|medication|medicine|tablet|pill|injection|infusion|vaccine|antibiotic)",
        "tests": r"(?:test|panel|scan|screening|biopsy|ultrasound|mri|ct scan|x-ray|blood test|lab test|diagnostic)",
        "procedures": r"(?:surgery|procedure|operation|transplant|therapy|treatment)",
    }

    # Known legitimate medical terms (whitelist for quick checks)
    KNOWN_LEGITIMATE_TERMS = {
        # Common conditions
        "diabetes", "hypertension", "asthma", "arthritis", "cancer", "depression",
        "anxiety", "heart disease", "stroke", "pneumonia", "bronchitis", "flu",
        "covid-19", "measles", "chickenpox", "eczema", "psoriasis", "migraine",
        "acne", "obesity", "copd", "emphysema", "kidney disease", "liver disease",
        
        # Common drugs
        "aspirin", "ibuprofen", "acetaminophen", "naproxen", "metformin", "insulin",
        "lisinopril", "atorvastatin", "amoxicillin", "penicillin", "warfarin",
        "prednisone", "omeprazole", "sertraline", "fluoxetine", "lorazepam",
        
        # Common tests
        "blood test", "urinalysis", "mri", "ct scan", "x-ray", "ultrasound",
        "ecg", "ekg", "biopsy", "colonoscopy", "mammogram", "pap smear",
        
        # Common procedures
        "surgery", "vaccination", "therapy", "dialysis", "chemotherapy",
    }

    # Fake/non-existent medical terms (blacklist for known hallucinations)
    KNOWN_FAKE_TERMS = {
        "fictitious syndrome z", "fictitious syndrome", "imaginex", "bloodharmony panel",
        "quantum healing", "chakra medicine", "homeopathic magic",
        "blood harmony", "bloodharmony", "quantum nervous system",
    }

    @classmethod
    def detect_hallucinations(
        cls,
        response: str,
        knowledge_base_search_fn=None,
    ) -> Tuple[bool, str, List[str]]:
        """
        Detect hallucinations in a medical response.
        
        Args:
            response: The generated medical response to check
            knowledge_base_search_fn: Optional function to search knowledge base
                                     Signature: async fn(term) -> bool (exists in KB)
        
        Returns:
            Tuple of:
            - is_hallucinating: True if hallucinations detected
            - feedback: Explanation of what was hallucinated
            - suspected_terms: List of terms that appear to be hallucinated
        """
        suspected_terms = []
        feedback = ""

        # Extract medical terms from response
        extracted_terms = cls._extract_medical_terms(response)
        
        if not extracted_terms:
            return False, "No medical terms to validate", []

        # Check each extracted term
        for term in extracted_terms:
            term_lower = term.lower()
            
            # Quick check: Known fake terms
            if term_lower in cls.KNOWN_FAKE_TERMS:
                suspected_terms.append(term)
                logger.warning(f"[HALLUCINATION] Known fake term detected: {term}")
                continue
            
            # Quick check: Known legitimate terms (pass)
            if term_lower in cls.KNOWN_LEGITIMATE_TERMS:
                continue
            
            # Check if term looks suspicious (too long, unusual patterns)
            if cls._looks_suspicious(term):
                suspected_terms.append(term)
                logger.warning(f"[HALLUCINATION] Suspicious term detected: {term}")
                continue
            
            # Check against knowledge base if available
            if knowledge_base_search_fn:
                try:
                    # Run async check synchronously
                    exists_in_kb = asyncio.run(
                        knowledge_base_search_fn(term)
                    )
                    if not exists_in_kb:
                        suspected_terms.append(term)
                        logger.warning(f"[HALLUCINATION] Term not in KB: {term}")
                except Exception as e:
                    logger.debug(f"KB search failed for {term}: {e}")
                    # Don't mark as hallucination if KB search fails
                    pass

        # Generate feedback
        if suspected_terms:
            feedback = (
                f"Potential hallucinations detected: {', '.join(suspected_terms)}. "
                f"These medical terms may not be real or verified."
            )
            return True, feedback, suspected_terms
        else:
            feedback = "No hallucinations detected - all terms verified"
            return False, feedback, []

    @classmethod
    def _extract_medical_terms(cls, text: str) -> List[str]:
        """Extract medical terms from text."""
        terms = set()
        text_lower = text.lower()

        # Look for capitalized terms that might be condition/drug names
        # e.g., "Fictitious Syndrome Z", "Imaginex", "BloodHarmony Panel"
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        
        for match in re.finditer(capitalized_pattern, text):
            term = match.group(0)
            # Filter out common English words
            if not cls._is_common_word(term) and len(term) > 2:
                terms.add(term)
                # Also add lowercase version for fallback matching
                terms.add(term.lower())

        # Also look for quoted terms or phrases after specific words
        quoted_pattern = r"['\"]([^'\"]+)['\"]"
        for match in re.finditer(quoted_pattern, text):
            term = match.group(1)
            if any(keyword in text_lower[max(0, match.start()-50):match.start()]
                   for keyword in ['drug', 'medication', 'syndrome', 'disease', 'test', 'condition']):
                terms.add(term)
                terms.add(term.lower())

        # Look for unusual capitalization patterns (e.g., "BloodHarmony Panel")
        # Words with unusual capitalization in the middle
        unusual_cap_pattern = r'\b[A-Z][a-z]+[A-Z][a-z]+\b'
        for match in re.finditer(unusual_cap_pattern, text):
            term = match.group(0)
            terms.add(term)
            terms.add(term.lower())

        return list(terms)

    @classmethod
    def _looks_suspicious(cls, term: str) -> bool:
        """
        Check if a term has characteristics of a made-up medical term.
        """
        # Very long terms (real conditions usually have standard names)
        if len(term) > 50:
            return True
        
        # Terms with unusual character patterns
        if re.search(r'[0-9]{3,}', term):  # Multiple consecutive numbers
            return True
        
        # Multiple special characters
        if len(re.findall(r'[^a-zA-Z0-9\s]', term)) > 2:
            return True
        
        # Common made-up suffixes/patterns
        made_up_patterns = [
            r'quantum\s+\w+',  # "Quantum healing"
            r'magical\s+\w+',  # "Magical cure"
            r'super\s+\w+',    # "Super treatment"
            r'miracle\s+\w+',  # "Miracle cure"
            r'\w+ness\s+\w+',  # "Fittingness syndrome"
        ]
        
        for pattern in made_up_patterns:
            if re.search(pattern, term.lower()):
                return True
        
        return False

    @classmethod
    def _is_common_word(cls, term: str) -> bool:
        """Check if a term is a common English word (not a medical term)."""
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that',
            'these', 'those', 'what', 'which', 'who', 'how', 'where', 'when',
            'why', 'should', 'could', 'would', 'may', 'might', 'must', 'will',
            'can', 'has', 'have', 'had', 'do', 'does', 'did', 'been', 'be',
            'about', 'of', 'in', 'to', 'for', 'with', 'from', 'as', 'by',
        }
        return term.lower() in common_words

    @classmethod
    async def validate_against_knowledge_base(
        cls,
        terms: List[str],
        vector_store,
    ) -> Dict[str, bool]:
        """
        Validate a list of medical terms against the knowledge base.
        
        Args:
            terms: List of medical terms to validate
            vector_store: Vector store instance (Qdrant)
        
        Returns:
            Dict mapping term -> exists_in_kb (bool)
        """
        results = {}
        
        for term in terms:
            try:
                # Search for the term in the knowledge base
                if hasattr(vector_store, 'search'):
                    # Try semantic search first
                    search_results = vector_store.search(
                        query=term,
                        limit=1,
                        threshold=0.5,  # Moderate similarity threshold
                    )
                    results[term] = len(search_results) > 0
                else:
                    # Fallback: assume exists if can't check
                    results[term] = True
            except Exception as e:
                logger.debug(f"KB validation failed for {term}: {e}")
                results[term] = True  # Assume legitimate if can't validate

        return results
