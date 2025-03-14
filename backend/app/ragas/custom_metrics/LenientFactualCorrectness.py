import re
import typing as t
from dataclasses import dataclass, field

import pandas as pd
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
        # First try to extract numbers
        response_val = self.extract_number(sample.response)
        reference_val = self.extract_number(sample.reference)

        # If both texts don't contain numbers, compare them as text
        if response_val is None and reference_val is None:
            # Simple text similarity for non-numeric responses
            response_words = set(sample.response.lower().split())
            reference_words = set(sample.reference.lower().split())
            
            if not response_words or not reference_words:
                return 0.0
                
            # Calculate Jaccard similarity
            intersection = len(response_words.intersection(reference_words))
            union = len(response_words.union(reference_words))
            return intersection / union if union > 0 else 0.0

        # If one has numbers and the other doesn't, return 0
        if response_val is None or reference_val is None:
            return 0.0

        # Compare numbers
        diff = abs(response_val - reference_val)
        relative_error = diff / reference_val if reference_val != 0 else float('inf')
        
        # Award a perfect 1.0 only if they match exactly
        if diff == 0:
            return 1.0
        else:    
            return max(1.0 - (relative_error * 9.9), 0.0)

    def extract_number(self, text: str) -> float:
        if not text:
            return None
            
        try:
            # Look for numbers in the text
            matches = re.findall(r'(\d+\.?\d*)', text)
            if not matches:
                return None
            # Return the first number found
            return float(matches[0])
        except (ValueError, AttributeError):
            return None
