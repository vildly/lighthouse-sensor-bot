import pandas as pd
import json
from ragas import evaluate, EvaluationDataset
from ragas.metrics import LLMContextRecall, Faithfulness, SemanticSimilarity

# from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._string import NonLLMStringSimilarity
from ragas.metrics import RougeScore
from ragas.metrics import StringPresence
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from pathlib import Path
import datetime
import requests
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from app.ragas.custom_metrics.bleu_score import BleuScore
import argparse
from typing import Callable, Optional
import re
from app.helpers.extract_answer import extract_answer_for_evaluation
import logging


logger = logging.getLogger(__name__)

load_dotenv()
# this script is used to evaluate the performance of the agent on the synthetic dataset.
API_URL = os.getenv("API_URL")
RAGAS_APP_TOKEN = os.getenv("RAGAS_APP_TOKEN")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LLM and Embeddings wrappers
if DEEPSEEK_API_KEY:
    print("Using DeepSeek API key")
    evaluator_llm = LangchainLLMWrapper(
        ChatDeepSeek(model="deepseek-chat", temperature=0)
    )
if not DEEPSEEK_API_KEY:
    print("Using OpenAI API key")
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))

evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())


def run_test_case(query, llm_model_id, test_no=None):
    """Run a single test case through the API"""
    
    api_url = f"{API_URL}/api/query"
    try:
        response = requests.post(
            api_url,
            json={
                "question": query,
                "source_file": "ferry_trips_data.csv",
                "llm_model_id": llm_model_id,
            },
        )
        response.raise_for_status()

        response_data = response.json()
        agent_response = response_data.get("content")
        full_response = response_data.get("full_response")
        sql_queries = response_data.get("sql_queries", [])
        token_usage = response_data.get("token_usage")

        if agent_response is None:
            print(
                f"Error: No 'content' key found in the API response for query: {query}"
            )
            return None, None, False, None

        # Format contexts including SQL queries and full response
        contexts = []
        for sql in sql_queries:
            contexts.append(f"SQL Query: {sql}")
        contexts.append(f"Agent Reasoning and Response: {full_response}")

        return agent_response, contexts, True, token_usage

    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, None, False, None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, None, False, None


def load_synthetic_test_cases():
    """Load synthetic test cases from JSON file"""
    test_cases_path = Path("app/ragas/test_cases/synthetic_test_cases.json")
    try:
        with open(test_cases_path, "r") as f:
            test_cases = json.load(f)
        return test_cases
    except FileNotFoundError:
        print(f"Error: {test_cases_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {test_cases_path}.")
        return None


def save_failed_test(test_case, llm_model_id, error_response=None):
    """Save tests that resulted in a 500 status code to a file"""

    # Create output directory if it doesn't exist
    output_dir = os.path.join("app", "ragas", "failed_tests")
    os.makedirs(output_dir, exist_ok=True)

    # Create a filename with timestamp and test number
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    test_no = test_case.get("test_no", "unknown")
    filename = f"failed_test_{test_no}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Prepare data to save
    failed_test_data = {
        "test_case": test_case,
        "model_id": llm_model_id,
        "error": str(error_response),
        "timestamp": timestamp,
    }

    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(failed_test_data, f, indent=2, ensure_ascii=False)

    print(f"Saved failed test to {filepath}")
    return filepath


def save_ragas_failed_test(test_case, llm_model_id, response, context, error=None):
    """Save tests where RAGAS evaluation failed"""

    # Create output directory if it doesn't exist
    output_dir = os.path.join("app", "ragas", "ragas_eval_failed")
    os.makedirs(output_dir, exist_ok=True)

    # Create a filename with timestamp and test number
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    test_no = test_case.get("test_no", "unknown")
    filename = f"ragas_eval_failed_{test_no}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Prepare data to save
    failed_data = {
        "test_case": test_case,
        "model_id": llm_model_id,
        "response": response,
        "context": context,
        "error": str(error),
        "timestamp": timestamp,
    }

    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(failed_data, f, indent=2, ensure_ascii=False)

    print(f"Saved RAGAS evaluation failure to {filepath}")
    return filepath


def evaluate_single_test(
    test_case, response, context, reference_contexts, llm_model_id
):
    """Evaluate a single test with RAGAS and return the results"""
    try:
        # Create single test dataset
        test_data = pd.DataFrame(
            {
                "user_input": [test_case["query"]],
                "reference": [test_case["ground_truth"]],
                "response": [response],
                "retrieved_contexts": [reference_contexts],
            }
        )

        # Create evaluation dataset
        eval_dataset = EvaluationDataset.from_pandas(test_data)

        # Define metrics
        metrics = [
            LenientFactualCorrectness(),
            SemanticSimilarity(embeddings=evaluator_embeddings),
            LLMContextRecall(llm=evaluator_llm),
            Faithfulness(llm=evaluator_llm),
            BleuScore(),
            NonLLMStringSimilarity(),
            RougeScore(),
            StringPresence(),
        ]

        # Run evaluation on single test
        result = evaluate(eval_dataset, metrics, llm=evaluator_llm)

        # Return success with results
        return True, result, None

    except Exception as e:
        logger.error(f"RAGAS evaluation failed for test {test_case['test_no']}: {e}")
        print(f"RAGAS evaluation failed for test {test_case['test_no']}: {e}")

        # Save the RAGAS failed test
        filepath = save_ragas_failed_test(test_case, llm_model_id, response, context, e)

        # Return failure with error
        return False, None, str(e)


def run_synthetic_evaluation(
    llm_model_id, progress_callback: Optional[Callable] = None
):
    """Run evaluation using the synthetic test cases"""
    logger.info("Starting run_synthetic_evaluation...")

    # Load synthetic test cases
    test_cases = load_synthetic_test_cases()
    logger.info(f"Loaded test cases: {test_cases is not None}")

    if test_cases is None:
        logger.error("No test cases loaded - returning None")
        return None, None

    # Create categories for tests
    api_success_ragas_success = []  # API call success + RAGAS evaluation success
    api_success_ragas_failed = []  # API call success + RAGAS evaluation failure
    api_failed_tests = []  # API call failure

    # Store RAGAS results
    all_ragas_results = []

    logger.info(f"Number of test cases: {len(test_cases)}")

    # Process each test case
    for i, test_case in enumerate(test_cases):
        if progress_callback:
            progress_callback(
                i, len(test_cases), f"Processing test {i+1}/{len(test_cases)}"
            )

        query = test_case["query"]
        logger.info(f"Processing test case {test_case['test_no']}: {query[:50]}...")

        # Run the API call
        response, context, api_call_success, token_usage = run_test_case(
            query, llm_model_id, test_case.get("test_no")
        )
        logger.info(f"API call success: {api_call_success}")

        if api_call_success:
            # Run RAGAS evaluation on this single test
            ragas_success, ragas_result, ragas_error = evaluate_single_test(
                test_case,
                response,
                context,
                test_case["reference_contexts"],
                llm_model_id,
            )

            # Common test result data
            test_result = {
                "test_no": test_case["test_no"],
                "query": query,
                "ground_truth": test_case["ground_truth"],
                "response": response,
                "context": context,
                "reference_contexts": test_case["reference_contexts"],
                "api_call_success": True,
                "token_usage": token_usage,
            }

            if ragas_success:
                # API call and RAGAS both successful
                test_result["ragas_evaluated"] = True
                test_result["ragas_results"] = ragas_result
                api_success_ragas_success.append(test_result)
                all_ragas_results.append(ragas_result)
            else:
                # API call success but RAGAS failed
                test_result["ragas_evaluated"] = False
                test_result["ragas_error"] = ragas_error
                api_success_ragas_failed.append(test_result)
        else:
            # API call failed
            logger.warning(f"Test {test_case['test_no']} failed with error: {response}")
            print(f"Test {test_case['test_no']} failed with error: {response}")

            # Save failed test
            filepath = save_failed_test(test_case, llm_model_id, response)

            # Add to API failed tests list
            api_failed_tests.append(
                {
                    "test_no": test_case["test_no"],
                    "query": query,
                    "ground_truth": test_case["ground_truth"],
                    "error": str(response),
                    "saved_path": filepath,
                    "api_call_success": False,
                    "ragas_evaluated": False,
                }
            )

    # Report on counts for each category
    logger.info(
        f"Tests completed: {len(api_success_ragas_success)} successful + evaluated, "
        + f"{len(api_success_ragas_failed)} successful but RAGAS failed, "
        + f"{len(api_failed_tests)} API call failed"
    )

    # Combine all results into a single DataFrame for reporting
    results = []
    results.extend(api_success_ragas_success)
    results.extend(api_success_ragas_failed)
    results.extend(api_failed_tests)

    # Create final DataFrame
    all_tests_df = pd.DataFrame(results)

    # Check if we have any successful RAGAS evaluations
    if all_ragas_results:
        # Combine all successful RAGAS results
        combined_ragas_results = all_ragas_results[0]

        # If there are multiple results, try to combine them
        if len(all_ragas_results) > 1:
            for i in range(1, len(all_ragas_results)):
                try:
                    for metric_key in combined_ragas_results.keys():
                        if metric_key in all_ragas_results[i]:
                            # Average the values for each metric
                            combined_ragas_results[metric_key] = (
                                combined_ragas_results[metric_key]
                                + all_ragas_results[i][metric_key]
                            ) / 2
                except Exception as e:
                    logger.error(f"Error combining RAGAS results: {e}")

        return combined_ragas_results, all_tests_df
    else:
        # No successful RAGAS evaluations
        return None, all_tests_df

