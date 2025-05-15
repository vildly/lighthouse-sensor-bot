# app/tests/utils/test_number_comparison.py
import argparse
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness


def test_number_comparison(num1, num2):
    """
    Test the number comparison function with custom values.

    Args:
        num1 (float): First number to compare
        num2 (float): Second number to compare (treated as reference/ground truth)

    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    # Create metric instance
    metric = LenientFactualCorrectness()

    # Calculate the comparison score
    score = metric.compare_numbers(num1, num2)

    # Calculate relative error for explanation
    relative_error = abs(num1 - num2) / max(abs(num2), 1e-10)
    absolute_diff = abs(num1 - num2)
    percentage_diff = relative_error * 100

    # Print detailed information
    print(f"Comparing {num1} to {num2}:")
    print(f"Absolute difference: {absolute_diff}")
    print(f"Relative difference: {percentage_diff:.2f}%")
    print(f"Similarity score: {score:.4f}")

    return score


if __name__ == "__main__":
    num1 = 764.43
    num2 = 743.98

    test_number_comparison(num1, num2)
