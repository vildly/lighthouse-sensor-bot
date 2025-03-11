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
        pass

    def supports_sample_type(self, sample_type) -> bool:
        return sample_type is SingleTurnSample

    async def _single_turn_ascore(self, sample: SingleTurnSample, callbacks=None) -> float:
        response_val = self.extract_number(sample.response)
        reference_val = self.extract_number(sample.reference)

        if response_val is None or reference_val is None:
            return 0.0

        diff = abs(response_val - reference_val)
        if diff < 0.01:
            return 1.0
        elif diff < 0.1:
            return 1.0 - (diff / 0.1)
        else:
            return 0.0

    def extract_number(self, text: str) -> float:
        match = re.search(r"([\d\.]+)", text)
        if match:
            return float(match.group(1))
        return None