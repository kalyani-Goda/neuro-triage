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
            # Define anonymization operators
            operators = {
                "PERSON": {"type": "replace", "new_value": "[NAME]"},
                "EMAIL_ADDRESS": {"type": "replace", "new_value": "[EMAIL]"},
                "PHONE_NUMBER": {"type": "replace", "new_value": "[PHONE]"},
                "CREDIT_CARD": {"type": "replace", "new_value": "[CREDIT_CARD]"},
                "US_SSN": {"type": "replace", "new_value": "[SSN]"},
                "US_DRIVER_LICENSE": {"type": "replace", "new_value": "[LICENSE]"},
                "IBAN_CODE": {"type": "replace", "new_value": "[IBAN]"},
                "DATE_TIME": {"type": "replace", "new_value": "[DATE]"},
            }

            # Analyze first
            pii_results = self.analyzer.analyze(
                text=text,
                language="en",
                entities=list(operators.keys()),
            )

            # Anonymize
            anonymized_text = self.anonymizer.anonymize(
                text=text,
                analyzer_results=pii_results,
                operators=operators,
            ).text

            if pii_results:
                logger.info(f"PII masked in text ({len(pii_results)} entities)")

            return anonymized_text
        except Exception as e:
            logger.error(f"PII masking failed: {e}")
            return text

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
