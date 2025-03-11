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
        response_val = self.extract_number(sample.response)
        reference_val = self.extract_number(sample.reference)

        # If either has no numeric content, score 0.0
        
        # make this proportional, not just hard coded values!!!!!!
        if response_val is None or reference_val is None:
            return 0.0

        diff = abs(response_val - reference_val)
        
        # Award a perfect 1.0 only if they match exactly
        if diff == 0:
            return 1.0
        # Slight partial credit if difference < 0.01
        elif diff < 0.01:
            return 0.75
        # Minimal partial credit if difference < 0.05
        elif diff < 0.05:
            return 0.4
        # Otherwise 0.0
        return 0.0

    def extract_number(self, text: str) -> float:
        match = re.search(r"([\d\.]+)", text)
        if match:
            return float(match.group(1))
        return None
