import asyncio
import argparse
import os
import json
import aiohttp
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from ragas.dataset_schema import SingleTurnSample

async def test_factual_correctness(response, reference, query=""):
    """
    Test the LenientFactualCorrectness metric on a response and reference.
    
    Args:
        response (str): The generated response to evaluate
        reference (str): The reference (ground truth) answer
        query (str): The query/question (optional)
        
    Returns:
        float: Factual correctness score between 0.0 and 1.0
    """
    # Create the metric instance
    metric = LenientFactualCorrectness()
    metric.init()  # Initialize the API key
    
    # Create a sample with the response and reference
    sample = SingleTurnSample(
        user_input=query,
        response=response,
        reference=reference
    )
    
    # Extract the first relevant number from each text based on the query
    response_val = await metric.extract_first_number(response, query)
    reference_val = await metric.extract_first_number(reference, query)
    
    # Calculate the final score using the class method
    score = await metric._single_turn_ascore(sample)
    
    # Print information for debugging
    print(f"Query: {query}")
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
    parser.add_argument('--query', type=str, help='Query or question text', default='')

  
    
    # Example 1: Exact match
    # response = "The total cost was 116000 SEK"
    # reference  = "Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
    # query  = "What was the total fuel cost for ferry Jupiter in January 2024?"
    
    query = "What is the average speed of ferry Jupiter? (in km/h)"
    response = "The average speed of ferry Jupiter is: 11 km/h"
    reference = "Average speed in km/h is 11.55"
    
    
    asyncio.run(test_factual_correctness(response, reference, query))
  

if __name__ == "__main__":
    main()