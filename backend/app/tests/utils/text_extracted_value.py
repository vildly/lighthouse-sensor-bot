# app/tests/test_extracted_value.py
import asyncio
import os
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from ragas.dataset_schema import SingleTurnSample

async def test_extracted_value():
    # Create the metric instance
    metric = LenientFactualCorrectness()
    metric.api_key = os.environ.get("OPENROUTER_API_KEY")
    
    # Test data
    reference = "The average number of vehicles left at terminals in June for Furusundsleden is 5.01"
    response = "The average number of vehicles left at terminals in June for Furusundsleden is **5.006 vehicles**."
    query = "What's the average number of vehicles left at terminals in June for Furusundsleden (combine outbound and inboud)?"
    
    # Pre-register the extracted true value
    extracted_val = 5.01
    metric.register_extracted_true_value(reference, extracted_val)
    
    # Create a sample with the response and reference
    sample = SingleTurnSample(
        user_input=query,
        response=response,
        reference=reference
    )
    
    # Calculate the final score using the class method
    score = await metric._single_turn_ascore(sample)
    
    print(f"Query: {query}")
    print(f"Response: {response}")
    print(f"Reference: {reference}")
    print(f"Pre-registered value: {extracted_val}")
    print(f"Score: {score:.4f}")
    
    return score

if __name__ == "__main__":
    asyncio.run(test_extracted_value())