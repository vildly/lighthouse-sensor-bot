# app/tests/utils/text_extracted_value.py
import asyncio
import os
import json
import traceback
import random
from pathlib import Path
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness

async def test_extracted_value(iterations_per_test=10):
    """Test if the LLM extractor can extract the correct number from ground truth for all test cases
    
    Args:
        iterations_per_test (int): Number of times to run each test case (default: 10)
    """
    # Create the metric instance
    metric = LenientFactualCorrectness()
    metric.api_key = os.environ.get("OPENROUTER_API_KEY")
    if not metric.api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set")
        return None
    
    # Load all test cases from the JSON file
    test_cases_path = Path("app/ragas/test_cases/synthetic_test_cases.json")
    try:
        with open(test_cases_path, "r") as f:
            test_cases = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading test cases: {e}")
        return None
    
    print(f"Loaded {len(test_cases)} test cases, running each {iterations_per_test} times")
    
    # Test results container
    results = {
        "total_tests": len(test_cases) * iterations_per_test,
        "successful_extractions": 0,
        "failed_extractions": 0,
        "test_details": []
    }
    
    # Track per-test case success rates
    test_case_stats = {}
    
    # Run each test case multiple times
    for test_case in test_cases:
        test_no = test_case.get("test_no", "N/A")
        query = test_case["query"]
        ground_truth = test_case["ground_truth"]
        expected_value_str = test_case.get("extracted_true_value", "").strip()
        
        try:
            expected_value = float(expected_value_str)
        except (ValueError, TypeError) as e:
            print(f"Error converting expected value for test {test_no}: '{expected_value_str}', error: {e}")
            expected_value = None
            
        # Initialize stats for this test case
        test_case_stats[test_no] = {
            "successes": 0,
            "failures": 0,
            "total": iterations_per_test
        }
        
        print(f"\n==== Testing case {test_no}: {iterations_per_test} iterations ====")
        print(f"Query: {query}")
        print(f"Ground truth: {ground_truth}")
        print(f"Expected value: {expected_value}")
        
        # Run this test case multiple times
        for iteration in range(iterations_per_test):
            try:
                print(f"\nIteration {iteration+1}/{iterations_per_test} for test {test_no}")
                
                # Extract the actual value using the LLM
                try:
                    print(f"Calling LLM API to extract value...")
                    extracted_value = await metric.extract_first_number(ground_truth, query)
                    print(f"API call completed successfully")
                except Exception as e:
                    print(f"Error during LLM extraction: {e}")
                    traceback.print_exc()
                    extracted_value = None
                
                # Check if extraction is successful
                success = False
                if expected_value is not None and extracted_value is not None:
                    # Calculate relative difference
                    if expected_value == 0:
                        # Handle division by zero
                        success = extracted_value == 0
                    else:
                        rel_diff = abs(extracted_value - expected_value) / expected_value
                        success = rel_diff <= 0.00 # 0% difference
                
                # Store the result
                result = {
                    "test_no": test_no,
                    "iteration": iteration + 1,
                    "query": query,
                    "ground_truth": ground_truth,
                    "expected_value": expected_value,
                    "extracted_value": extracted_value,
                    "success": success
                }
                results["test_details"].append(result)
                
                # Update counters
                if success:
                    results["successful_extractions"] += 1
                    test_case_stats[test_no]["successes"] += 1
                else:
                    results["failed_extractions"] += 1
                    test_case_stats[test_no]["failures"] += 1
                    
                # Print the result for this iteration
                print(f"Iteration {iteration+1} - Extracted value: {extracted_value}, Success: {success}")
                
                # Add a small random delay between API calls to avoid rate limiting
                await asyncio.sleep(0.5 + random.random())
                
            except Exception as e:
                print(f"Unexpected error in iteration {iteration+1} for test {test_no}: {e}")
                traceback.print_exc()
                results["failed_extractions"] += 1
                test_case_stats[test_no]["failures"] += 1
    
    # Print summary
    print("\n==== Extraction Results Summary ====")
    print(f"Overall: {results['successful_extractions']}/{results['total_tests']} successful "
          f"({results['successful_extractions']/results['total_tests']*100:.1f}%)")
    
    # Print per-test case statistics
    print("\nPer-test case success rates:")
    for test_no, stats in test_case_stats.items():
        success_rate = (stats["successes"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"Test {test_no}: {stats['successes']}/{stats['total']} successful ({success_rate:.1f}%)")
    
    # List failed tests
    if results["failed_extractions"] > 0:
        print("\nSome extractions failed. Check test details for more information.")
    
    return results

if __name__ == "__main__":
    try:
        print("Starting extraction test for all test cases")
        asyncio.run(test_extracted_value(iterations_per_test=10))
        print("Test completed successfully")
    except Exception as e:
        print(f"Fatal error in test_extracted_value: {e}")
        traceback.print_exc()