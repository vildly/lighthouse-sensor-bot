import re
import typing as t
from dataclasses import dataclass, field
import numpy as np
from ragas import evaluate, EvaluationDataset
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import SingleTurnMetric, MetricType

@dataclass
class LenientFactualCorrectness(SingleTurnMetric):
    name: str = "lenient_factual_correctness"

    required_columns: t.Dict[MetricType, t.Set[str]] = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {"response", "reference"}
        }
    )

    def init(self, run_config=None) -> None:
        """No-op init required by SingleTurnMetric in RAGAS 0.2.14."""
        pass

    def supports_sample_type(self, sample_type) -> bool:
        return sample_type is SingleTurnSample

    async def _single_turn_ascore(self, sample: SingleTurnSample, callbacks=None) -> float:
        # First try simple number extraction to handle simple cases directly
        response_val = self.extract_first_number(sample.response)
        reference_val = self.extract_first_number(sample.reference)
        
        # If we have clean numbers with less than 5% difference, give a good score directly
        if response_val is not None and reference_val is not None:
            relative_diff = abs(response_val - reference_val) / max(abs(reference_val), 1e-10)
            if relative_diff < 0.05:  # Within 5% is good
                return 1.0 - relative_diff * 10  # Scale down slightly for small differences
        
        # Fall back to full extraction and matching for complex cases
        response_numbers = self.extract_all_numbers(sample.response)
        reference_numbers = self.extract_all_numbers(sample.reference)
        
        if not response_numbers or not reference_numbers:
            return 0.0

        # Match numbers without context restriction
        # Look for the closest matching number in the response to any reference number
        best_match = 0.0
        for ref_num, _ in reference_numbers:
            for resp_num, _ in response_numbers:
                similarity = self.compare_numbers(resp_num, ref_num)
                if similarity > best_match:
                    best_match = similarity
        
        return float(best_match)

    def extract_first_number(self, text: str) -> float:
        """Extract the first number in the text for simple cases."""
        if not text:
            return None
        
        # Look for decimal numbers
        match = re.search(r'(\d+\.\d+)', text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                pass
                
        # Fall back to any number
        match = re.search(r'(\d+)', text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                pass
                
        return None

    def extract_all_numbers(self, text: str) -> list[tuple[float, str]]:
        if not text:
            return []
        
        numbers_with_context = []
        # Improved pattern to better match decimal numbers
        pattern = r'(\b\d+\.\d+\b|\b\d+\b)'
        
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                number = float(match.group(1))
                # Get a window of text around the number (10 chars before and after)
                start = max(0, match.start() - 10)
                end = min(len(text), match.end() + 10)
                context = text[start:end].strip()
                numbers_with_context.append((number, context))
            except (ValueError, AttributeError):
                continue
                
        return numbers_with_context

    def compare_numbers(self, num1: float, num2: float) -> float:
        if num1 == num2:
            return 1.0
        
        relative_error = abs(num1 - num2) / max(abs(num2), 1e-10)
        
        return max(1.0 - (relative_error * 9.9), 0.0)