import asyncio
import argparse
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from ragas.dataset_schema import SingleTurnSample

async def test_factual_correctness(response, reference):
    """
    Test the LenientFactualCorrectness metric on a response and reference.
    
    Args:
        response (str): The generated response to evaluate
        reference (str): The reference (ground truth) answer
        
    Returns:
        float: Factual correctness score between 0.0 and 1.0
    """
    # Create the metric instance
    metric = LenientFactualCorrectness()
    
    # Create a sample with the response and reference
    sample = SingleTurnSample(
        question="",  # Not used for scoring
        response=response,
        reference=reference
    )
    
    # Extract the first number from each text
    response_val = metric.extract_first_number(response)
    reference_val = metric.extract_first_number(reference)
    
    # Calculate the final score
    score = await metric._single_turn_ascore(sample)
    
    # Print only the requested information
    print(f"Response: {response}")
    print(f"Extracted response value: {response_val}")
    print(f"Reference: {reference}")
    print(f"Extracted reference value: {reference_val}")
    print(f"Score: {score:.4f}")
    print("---")
    
    return score

def main():
    parser = argparse.ArgumentParser(description='Test LenientFactualCorrectness with custom inputs')
    parser.add_argument('--response', type=str, help='Response text to evaluate')
    parser.add_argument('--reference', type=str, help='Reference (ground truth) text')
    


    # Example 1: Exact match
    response1 = "The total cost was 254186.70 SEK"
    reference1 = "Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
    asyncio.run(test_factual_correctness(response1, reference1))
          


if __name__ == "__main__":
    main()