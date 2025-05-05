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
from .test_run_manager import create_test_run, update_test_run_status, ensure_experiment_runs_populated, mark_run_as_running, update_experiment_run_status
import ast
import math

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
        # --- Simulate 500 Error ---
        # Create a mock response object
        mock_response = requests.Response()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.url = api_url
        # Raise an HTTPError like requests would for a 5xx status
        mock_response.raise_for_status() 
        # --- End Simulation ---

        # --- Original Code (Commented out for simulation) ---
        # response = requests.post(
        #     api_url,
        #     json={
        #         "question": query,
        #         "source_file": "ferry_trips_data.csv",
        #         "llm_model_id": llm_model_id,
        #     },
        # )
        # response.raise_for_status()
        # 
        # response_data = response.json()
        # agent_response = response_data.get("content")
        # full_response = response_data.get("full_response")
        # sql_queries = response_data.get("sql_queries", [])
        # token_usage = response_data.get("token_usage")
        # 
        # if agent_response is None:
        #     print(
        #         f"Error: No 'content' key found in the API response for query: {query}"
        #     )
        #     return None, None, False, None
        # 
        # # Format contexts including SQL queries and full response
        # contexts = []
        # for sql in sql_queries:
        #     contexts.append(f"SQL Query: {sql}")
        # contexts.append(f"Agent Reasoning and Response: {full_response}")
        # 
        # return agent_response, contexts, True, token_usage
        # --- End Original Code ---

    except requests.exceptions.RequestException as e:
        # This block will now catch the simulated HTTPError
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

        RAGAS_APP_TOKEN = os.getenv("RAGAS_APP_TOKEN")

        if RAGAS_APP_TOKEN:
            print("Uploading results to RAGAS app")
            result.upload()

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
    llm_model_id, 
    progress_callback: Optional[Callable] = None,
    run_number: int = 1
):
    """Run evaluation using the synthetic test cases"""
    # Import moved here:
    from .test_run_manager import mark_run_as_running, update_experiment_run_status

    logger.info(f"Starting run_synthetic_evaluation (run #{run_number})...")

    # Load synthetic test cases
    test_cases = load_synthetic_test_cases()
    logger.info(f"Loaded test cases: {test_cases is not None}")

    if test_cases is None:
        logger.error("No test cases loaded - returning None")
        return None, None

    # Initialize counters
    successful = 0
    api_failed = 0
    ragas_failed = 0
    
    # Create collections for results
    api_success_ragas_success = []
    api_success_ragas_failed = []
    api_failed_tests = []
    all_ragas_results = []
    
    # REMOVE the create_test_run call - we'll use experiment_runs instead
    test_run_id = None  # Set to None instead of calling create_test_run
    logger.info("Using experiment_runs table for tracking")
    
    # For progress reporting
    total_test_cases = len(test_cases)
    
    # Process each test case
    for i, test_case in enumerate(test_cases):
        try:
            # Report progress
            if progress_callback:
                progress_callback(i, total_test_cases, f"Processing test case {i+1} of {total_test_cases}")
            
            # Extract values
            test_case_id = str(test_case.get("test_no", ""))
            query = test_case["query"]
            
            # Mark experiment run as running 
            mark_run_as_running(llm_model_id, test_case_id, run_number)
            
            # Run the API call
            response, context, api_call_success, token_usage = run_test_case(
                query, llm_model_id, test_case.get("test_no")
            )
            logger.info(f"API call success: {api_call_success}")

            # Store test_id for experiment tracking
            test_id = str(test_case.get('test_no', ''))

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
                    successful += 1
                    test_result["ragas_evaluated"] = True
                    test_result["ragas_results"] = ragas_result
                    api_success_ragas_success.append(test_result)
                    all_ragas_results.append(ragas_result)
                    update_experiment_run_status(
                        model_id=llm_model_id, 
                        test_case_id=test_case_id, 
                        run_number=run_number, 
                        status='success', 
                        error_message=None,
                        query_evaluation_id=test_id
                    )
                else:
                    # API call success but RAGAS failed
                    ragas_failed += 1
                    test_result["ragas_evaluated"] = False
                    test_result["ragas_error"] = ragas_error
                    api_success_ragas_failed.append(test_result)
                    update_experiment_run_status(
                        model_id=llm_model_id, 
                        test_case_id=test_case_id, 
                        run_number=run_number, 
                        status='failed', 
                        error_message="RAGAS evaluation failed",
                        query_evaluation_id=test_id
                    )
            else:
                # API call failed
                api_failed += 1
                
                # Create test result entry
                api_failed_tests.append({
                    "test_no": test_case["test_no"],
                    "query": query,
                    "ground_truth": test_case.get("ground_truth", ""),
                    "error": str(response),
                    "saved_path": None,
                    "api_call_success": False,
                    "ragas_evaluated": False,
                    "reference_contexts": test_case.get("reference_contexts", [])
                })
        except Exception as e:
            logger.error(f"Error processing test case {test_case['test_no']}: {e}")
            print(f"Error processing test case {test_case['test_no']}: {e}")

    # Update the end of the function
    # We're not updating test_run status since we're not using that table
    # Just log completion
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
    
    # Return the DataFrame of all individual test results and None for test_run_id
    return all_tests_df, None


def process_ragas_results(ragas_result, test_case):
    """Process RAGAS results into a consistent dictionary format"""
    # Map RAGAS metric names to our expected names
    metric_mapping = {
        'lenient_factual_correctness': 'factual_correctness',
        'semantic_similarity': 'semantic_similarity',
        'context_recall': 'context_recall',
        'faithfulness': 'faithfulness',
        'bleu_score': 'bleu_score',
        'non_llm_string_similarity': 'non_llm_string_similarity',
        'rouge_score(mode=fmeasure)': 'rogue_score',
        'string_present': 'string_present'
    }
    
    # Create evaluation results dictionary
    evaluation_data = {
        "retrieved_contexts": str(test_case["reference_contexts"]),
        "ground_truth": test_case["ground_truth"],
    }
    
    # Process RAGAS results - handle EvaluationResult object
    if hasattr(ragas_result, 'to_pandas'):
        # Convert to pandas DataFrame and then to dict
        df = ragas_result.to_pandas()
        if not df.empty:
            # Get the first row as a dictionary
            results_dict = df.iloc[0].to_dict()
        else:
            results_dict = {}
    elif isinstance(ragas_result, dict):
        results_dict = ragas_result
    else:
        # Convert to dictionary if it's not already
        results_str = str(ragas_result)
        if '{' in results_str and '}' in results_str:
            dict_part = results_str[results_str.find('{'): results_str.rfind('}')+1]
            try:
                import ast
                results_dict = ast.literal_eval(dict_part)
            except:
                results_dict = {"raw_results": results_str}
        else:
            results_dict = {"raw_results": results_str}
    
    # Map the metrics
    for ragas_key, our_key in metric_mapping.items():
        value = results_dict.get(ragas_key)
        if isinstance(value, float) and math.isnan(value):
            evaluation_data[our_key] = None
        else:
            evaluation_data[our_key] = value
            
    return evaluation_data
