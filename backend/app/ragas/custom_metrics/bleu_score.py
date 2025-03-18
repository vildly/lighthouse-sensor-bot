import nltk
from nltk.translate.bleu_score import sentence_bleu
import typing as t
from dataclasses import dataclass, field
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import SingleTurnMetric, MetricType

@dataclass
class BleuScore(SingleTurnMetric):
    name: str = "bleu_score"

    required_columns: t.Dict[MetricType, t.Set[str]] = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {"response", "reference"}
        }
    )

    def init(self, run_config=None) -> None:
        """No-op init required by SingleTurnMetric in RAGAS."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def supports_sample_type(self, sample_type) -> bool:
        return sample_type is SingleTurnSample

    async def _single_turn_ascore(self, sample: SingleTurnSample, callbacks=None) -> float:
        """Calculate BLEU score between reference and response."""
        if not sample.reference or not sample.response:
            return 0.0
            
        # Tokenize reference and response
        reference_tokens = [sample.reference.split()]
        response_tokens = sample.response.split()
        
        # Calculate BLEU score
        score = sentence_bleu(reference_tokens, response_tokens)
        
        return float(score)
