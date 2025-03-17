import nltk
from nltk.translate.bleu_score import sentence_bleu


def calculate_bleu(reference, candidate):
    reference_tokens = [reference.split()]
    candidate_tokens = candidate.split()

    score = sentence_bleu(reference_tokens, candidate_tokens)
    return score


if __name__ == "__main__":

    reference = """On January 18th, 2024, the ferry Jupiter on the Ljusteröleden route
  had a passenger car equivalent of 57.5 for both outbound and inbound trips,
  with a fuel consumption of 7.809388890461112 liters outbound and
  7.859527782155555 liters inbound. The outbound trip started at 18:21:22 and
  ended at 18:27:02, while the inbound trip started at 18:30:12 and ended at
  18:35:27. On January 28th, 2024, the same ferry had a passenger car equivalent
  of 46.5 for both outbound and inbound trips, with a fuel consumption of
  6.3114722644166665 liters outbound and 7.208888897983334 liters inbound. The
  outbound trip started at 18:00:42 and ended at 18:06:47, while the inbound
  trip started at 18:10:52 and ended at 18:15:47. This comparison shows that the
  ferry carried more vehicles and consumed more fuel on January 18th compared to
  January 28th."""

    candidate = """>-
  1. The ferry operations on the Ljusteröleden route on January 18th and January
  28th, 2024, primarily involved ordinary trips. The passenger car equivalents
  (PCE) for outbound trips ranged from 3.0 to 22.5, and for inbound trips, it
  ranged from 4.0 to 31.0. Fuel consumption for outbound trips ranged from
  approximately 6.28 to 9.45 liters, while for inbound trips, it ranged from
  5.61 to 8.13 liters, during the specified time intervals.


  2.
  """

    bleu_score = calculate_bleu(reference, candidate)
    print(f"BLEU Score: {bleu_score:.4f}")
