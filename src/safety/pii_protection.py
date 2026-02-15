"""PII (Personally Identifiable Information) protection."""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PIIProtector:
    """Protect PII in patient communications."""

    def __init__(self):
        """Initialize Presidio engines."""
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII entities in text."""
        try:
            results = self.analyzer.analyze(
                text=text,
                language="en",
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "US_SSN",
                    "US_DRIVER_LICENSE",
                    "IBAN_CODE",
                    "DATE_TIME",
                ],
            )

            pii_list = [
                {
                    "entity_type": result.entity_type,
                    "value": text[result.start : result.end],
                    "confidence": result.score,
                }
                for result in results
            ]

            if pii_list:
                logger.warning(f"PII detected: {[p['entity_type'] for p in pii_list]}")

            return pii_list
        except Exception as e:
            logger.error(f"PII detection failed: {e}")
            return []

    def mask_pii(self, text: str) -> str:
        """Mask/anonymize PII in text."""
        try:
            # Analyze first
            pii_results = self.analyzer.analyze(
                text=text,
                language="en",
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "US_SSN",
                    "US_DRIVER_LICENSE",
                    "IBAN_CODE",
                    "DATE_TIME",
                ],
            )

            if not pii_results:
                return text

            # Build anonymization operators dict with correct format
            operators = {}
            for entity in ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", 
                          "US_SSN", "US_DRIVER_LICENSE", "IBAN_CODE", "DATE_TIME"]:
                if entity == "PERSON":
                    operators[entity] = {"type": "replace", "new_value": "[NAME]"}
                elif entity == "EMAIL_ADDRESS":
                    operators[entity] = {"type": "replace", "new_value": "[EMAIL]"}
                elif entity == "PHONE_NUMBER":
                    operators[entity] = {"type": "replace", "new_value": "[PHONE]"}
                elif entity == "CREDIT_CARD":
                    operators[entity] = {"type": "replace", "new_value": "[CREDIT_CARD]"}
                elif entity == "US_SSN":
                    operators[entity] = {"type": "replace", "new_value": "[SSN]"}
                elif entity == "US_DRIVER_LICENSE":
                    operators[entity] = {"type": "replace", "new_value": "[LICENSE]"}
                elif entity == "IBAN_CODE":
                    operators[entity] = {"type": "replace", "new_value": "[IBAN]"}
                elif entity == "DATE_TIME":
                    operators[entity] = {"type": "replace", "new_value": "[DATE]"}
                else:
                    operators[entity] = {"type": "replace", "new_value": f"[{entity}]"}

            # Anonymize - use replace operator
            anonymized_text = self.anonymizer.anonymize(
                text=text,
                analyzer_results=pii_results,
                operators=operators,
            ).text

            logger.info(f"PII masked in text ({len(pii_results)} entities)")
            return anonymized_text
            
        except Exception as e:
            logger.error(f"PII masking failed: {e}")
            # Fallback: simple regex-based masking
            import re
            masked = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', text)
            masked = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', masked)
            masked = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', masked)
            return masked

    def check_pii_exposure(self, text: str) -> bool:
        """Check if text contains any PII."""
        try:
            results = self.analyzer.analyze(
                text=text,
                language="en",
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "US_SSN",
                    "US_DRIVER_LICENSE",
                    "IBAN_CODE",
                ],
            )
            return len(results) > 0
        except Exception as e:
            logger.error(f"PII check failed: {e}")
            return False


# Global PII protector instance
pii_protector = PIIProtector()
