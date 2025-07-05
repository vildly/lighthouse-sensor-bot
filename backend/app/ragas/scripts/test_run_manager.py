import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import time
from enum import Enum
from app.conf.postgres import get_cursor
import ast
import math
import pandas as pd
from app.helpers.save_query_to_db import save_query_with_eval_to_db
from flask_socketio import emit
from app.conf.websocket import socketio
from flask import has_app_context

# Create and configure logger with a direct stream handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Check if handlers already exist to avoid duplicates
if not logger.handlers:
    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Ensure our logger doesn't propagate to parent
    logger.propagate = False

def make_serializable(obj):
    """Recursively convert any non-serializable objects to serializable format"""
    from ragas.dataset_schema import SingleTurnSample
    
    if isinstance(obj, SingleTurnSample):
        # Convert SingleTurnSample to dict representation
        return str(obj)
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(item) for item in obj)
    elif hasattr(obj, '_repr_dict'):
        return obj._repr_dict
    elif hasattr(obj, 'to_dict') and callable(obj.to_dict):
        return make_serializable(obj.to_dict())
    else:
        # For any other types, try to convert to basic types
        try:
            import json
            json.dumps(obj)  # Test if it's serializable
            return obj
        except (TypeError, ValueError):
            return str(obj)

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_RETRIES_REACHED = "max_retries_reached"

class TestRunManager:
    """
    Manages the execution of test runs, including retry logic for failed tests.
    Tracks the status of each test case and records attempt history in the database.
    """
    
    def __init__(self, model_id: str, number_of_runs: int, max_retries: int = 3):
        """
        Initialize the test run manager.
        
        Args:
            model_id (str): The ID of the model being tested
            number_of_runs (int): Number of times each test should be run successfully
            max_retries (int): Maximum number of retry attempts for failed tests
        """
        self.model_id = model_id
        self.number_of_runs = number_of_runs
        self.max_retries = max_retries
        
        # Dict structure: {test_case_id: {run_number: {status, retry_count}}}
        self.test_status: Dict[str, Dict[int, Dict[str, Any]]] = {}
        
        # Track which evaluations were successful for reporting
        self.successful_evaluations: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized TestRunManager for model {model_id} with {number_of_runs} runs per test and max {max_retries} retries")
        
    def initialize_test_runs(self, test_cases: List[Dict[str, Any]]) -> None:
        """
        Initialize all test cases with pending status for each required run.
        
        Args:
            test_cases: List of test cases to run
        """
        for test_case in test_cases:
            test_id = str(test_case.get("test_no", "unknown"))
            self.test_status[test_id] = {}
            
            for run_number in range(1, self.number_of_runs + 1):
                self.test_status[test_id][run_number] = {
                    "status": TestStatus.PENDING,
                    "retry_count": 0,
                    "test_case": test_case
                }
        
        logger.info(f"Initialized {len(test_cases)} test cases for {self.number_of_runs} runs each")
        self._log_test_status_summary()
    
    def get_next_pending_test(self) -> Optional[Tuple[str, int, Dict[str, Any]]]:
        """
        Get the next pending test case that should be run.
        
        Returns:
            Tuple of (test_id, run_number, test_case) or None if no pending tests
        """
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                if run_info["status"] == TestStatus.PENDING:
                    return test_id, run_number, run_info["test_case"]
        return None
    
    def all_tests_completed(self) -> bool:
        """
        Check if all tests are completed (either success or max retries reached).
        
        Returns:
            True if all tests are completed, False otherwise
        """
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                if run_info["status"] not in [TestStatus.SUCCESS, TestStatus.MAX_RETRIES_REACHED]:
                    return False
        return True
    
    def mark_test_running(self, test_id: str, run_number: int) -> None:
        """
        Mark a test as running.
        
        Args:
            test_id: ID of the test
            run_number: Run number for the test
        """
        self.test_status[test_id][run_number]["status"] = TestStatus.RUNNING
        
    def mark_test_success(self, test_id: str, run_number: int, query_evaluation_id: Optional[int] = None) -> None:
        """
        Mark a test as successful.
        
        Args:
            test_id: ID of the test
            run_number: Run number for the test
            query_evaluation_id: ID of the query evaluation in the database
        """
        run_info = self.test_status[test_id][run_number]
        run_info["status"] = TestStatus.SUCCESS
        retry_count = run_info["retry_count"]
        
        # Record the successful attempt
        self._record_attempt_history(
            test_id, run_number, retry_count, 
            "success", None, query_evaluation_id
        )
        
        logger.info(f"Test {test_id} (run {run_number}) marked as successful after {retry_count} retries")
    
    def mark_test_failed(self, test_id: str, run_number: int, error_message: str) -> None:
        """
        Mark a test as failed and increment retry count.
        If max retries reached, mark as MAX_RETRIES_REACHED.
        
        Args:
            test_id: ID of the test
            run_number: Run number for the test
            error_message: Error message from the failure
        """
        run_info = self.test_status[test_id][run_number]
        
        # Increment retry count
        run_info["retry_count"] += 1
        retry_count = run_info["retry_count"]
        
        # Record the failed attempt
        self._record_attempt_history(
            test_id, run_number, retry_count - 1,  # Record the attempt that just failed
            "failed", error_message
        )
        
        # Check if max retries reached
        if retry_count >= self.max_retries:
            run_info["status"] = TestStatus.MAX_RETRIES_REACHED
            logger.warning(
                f"Test {test_id} (run {run_number}) reached max retries ({self.max_retries}): {error_message}"
            )
            
            # Record final status as max retries reached
            self._record_attempt_history(
                test_id, run_number, retry_count,
                "max_retries_reached", f"Max retries ({self.max_retries}) reached: {error_message}"
            )
        else:
            # Reset to pending for next attempt
            run_info["status"] = TestStatus.PENDING
            logger.info(
                f"Test {test_id} (run {run_number}) failed, will retry ({retry_count}/{self.max_retries}): {error_message}"
            )
    
    def add_successful_evaluation(self, evaluation_result: Dict[str, Any]) -> None:
        """Add a successful evaluation result to the tracking list"""
        self.successful_evaluations.append(evaluation_result)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the test run status.
        
        Returns:
            Dictionary with summary information
        """
        status_counts = {status.value: 0 for status in TestStatus}
        retry_total = 0
        successful_test_ids = set()
        failed_test_ids = set()
        
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                status_counts[run_info["status"].value] += 1
                retry_total += run_info["retry_count"]
                
                if run_info["status"] == TestStatus.SUCCESS:
                    successful_test_ids.add(test_id)
                elif run_info["status"] == TestStatus.MAX_RETRIES_REACHED:
                    failed_test_ids.add(test_id)
        
        return {
            "model_id": self.model_id,
            "total_tests": len(self.test_status) * self.number_of_runs,
            "successful_tests": status_counts[TestStatus.SUCCESS.value],
            "failed_tests": status_counts[TestStatus.MAX_RETRIES_REACHED.value],
            "pending_tests": status_counts[TestStatus.PENDING.value],
            "running_tests": status_counts[TestStatus.RUNNING.value],
            "total_retries": retry_total,
            "successful_test_ids": list(successful_test_ids),
            "failed_test_ids": list(failed_test_ids)
        }
    
    def _record_attempt_history(self, test_id: str, run_number: int, retry_count: int,
                               status: str, error_message: Optional[str] = None,
                               query_evaluation_id: Optional[int] = None) -> None:
        """Record an attempt in the run_attempt_history table"""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.run_attempt_history
                    (model_id, test_case_id, run_number, attempt_status, 
                     error_message, query_evaluation_id, retry_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.model_id,
                        test_id,
                        run_number,
                        status,
                        error_message,
                        query_evaluation_id,
                        retry_count
                    )
                )
                logger.debug(
                    f"Recorded attempt history: model={self.model_id}, "
                    f"test={test_id}, run={run_number}, status={status}, retry={retry_count}"
                )
        except Exception as e:
            logger.error(f"Error recording attempt history: {e}")
    
    def _log_test_status_summary(self) -> None:
        """Log a summary of the current test status counts"""
        status_counts = {status.value: 0 for status in TestStatus}
        retry_counts = {i: 0 for i in range(self.max_retries + 1)}
        
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                status_counts[run_info["status"].value] += 1
                retry_counts[run_info["retry_count"]] += 1
        
        logger.info(f"Test status summary: {status_counts}")
        logger.info(f"Retry counts: {retry_counts}")


def parse_test_selection(test_selection: str) -> List[int]:
    """
    Parse test selection string and return list of test indices.
    
    Examples:
        "1" -> [1]
        "1,3,5" -> [1, 3, 5]  
        "1-3" -> [1, 2, 3]
        "1,3,7-10" -> [1, 3, 7, 8, 9, 10]
    """
    if not test_selection:
        return []
    
    indices = []
    parts = test_selection.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle range (e.g., "1-3")
            try:
                start, end = part.split('-', 1)
                start_idx = int(start.strip())
                end_idx = int(end.strip())
                indices.extend(range(start_idx, end_idx + 1))
            except ValueError:
                print(f"Warning: Invalid range format '{part}', skipping")
                continue
        else:
            # Handle single number
            try:
                indices.append(int(part))
            except ValueError:
                print(f"Warning: Invalid test number '{part}', skipping")
                continue
    
    return sorted(list(set(indices)))  # Remove duplicates and sort

def execute_test_runs(model_id: str, number_of_runs, 
                     max_retries, progress_callback=None, test_data=None, test_selection=None):
    """
    Main function to execute all test runs with retry logic.
    
    Args:
        model_id: The model ID to test
        number_of_runs: Number of successful runs needed for each test
        max_retries: Maximum retry attempts per test
        progress_callback: Optional callback function for progress updates
        test_data: Optional pandas DataFrame containing test data (to avoid circular imports)
        test_selection: Optional string specifying which tests to run (e.g., "1", "1,3,5", "1-3")
    
    Returns:
        Tuple of (combined_ragas_results, all_tests_df)
    """
    # Ensure this message is printed directly as well as logged
    startup_msg = f"STARTING TEST RUNS for model {model_id} with {number_of_runs} runs per test"
    print(startup_msg)
    logger.info(startup_msg)
    
    # Import here to avoid circular imports
    from app.ragas.scripts.synthetic_ragas_tests import (
        load_synthetic_test_cases, 
        run_test_case, 
        evaluate_single_test
    )
    from app.helpers.save_query_to_db import save_query_with_eval_to_db
    
    # Load test cases - either from test_data parameter or by loading them
    test_cases = []
    if test_data is not None:
        # Convert DataFrame to list of dictionaries
        test_cases = test_data.to_dict(orient='records')
    else:
        test_cases = load_synthetic_test_cases()
    
    if not test_cases:
        logger.error("No test cases loaded")
        return None, None
    
    # Filter test cases based on test_selection if provided
    if test_selection:
        test_indices = parse_test_selection(test_selection)
        filtered_test_cases = []
        for i, test_case in enumerate(test_cases, 1):
            if i in test_indices:
                filtered_test_cases.append(test_case)
        test_cases = filtered_test_cases
        print(f"Filtered to {len(test_cases)} test cases based on selection: {test_selection}")
    
    # Initialize test run manager
    run_manager = TestRunManager(model_id, number_of_runs, max_retries)
    run_manager.initialize_test_runs(test_cases)
    
    # Execute test runs until all are completed
    all_test_results = []
    all_ragas_results = []
    
    # After test cases are loaded, calculate total tests
    total_tests = len(test_cases)
    current_test_index = 0
    total_runs = total_tests * number_of_runs
    current_run = 0
    
    # Initial progress update
    try:
        socketio.emit('evaluation_progress', {
            'progress': 0,
            'total': total_runs,
            'percent': 0,
            'test_no': 0,
            'total_tests': total_tests,
            'iteration': 0,
            'total_iterations': number_of_runs,
            'message': f'Starting evaluation of {total_tests} tests with {number_of_runs} runs each'
        }, namespace='/query')
    except Exception as e:
        logger.error(f"Error emitting initial progress: {e}")
    
    while not run_manager.all_tests_completed():
        # Get next test to run
        next_test = run_manager.get_next_pending_test()
        if not next_test:
            logger.info("No more tests to run")
            break
        
        test_id, run_number, test_case = next_test
        
        # Update progress if callback provided
        if progress_callback:
            summary = run_manager.get_summary()
            completed_tests = summary["successful_tests"] + summary["failed_tests"]
            progress_callback(
                completed_tests,
                summary["total_tests"],
                f"Running test {test_id} (run {run_number}/{number_of_runs})",
                test_no=test_id,
                total_tests=summary["total_tests"],
                iteration=run_number,
                total_iterations=number_of_runs
            )
        
        # Mark test as running
        run_manager.mark_test_running(test_id, run_number)
        
        try:
            logger.info(f"Running test {test_id} (run {run_number}/{number_of_runs})")
            
            # Before the loop starts for a specific test
            current_test_index += 1
            
            try:
                socketio.emit('evaluation_progress', {
                    'progress': current_run,
                    'total': total_runs,
                    'percent': int((current_run / total_runs) * 100),
                    'test_no': test_id,
                    'total_tests': total_tests,
                    'iteration': run_number,
                    'total_iterations': number_of_runs,
                    'message': f'Running test {test_id}/{total_tests} iteration {run_number}/{number_of_runs}'
                }, namespace='/query')
            except Exception as e:
                logger.error(f"Error emitting test progress: {e}")
            
            # Run the test case
            query = test_case["query"]
            response, context, api_call_success, token_usage, tool_calls = run_test_case(
                query, model_id, test_case.get("test_no")
            )

            # --- Extract tool calls ---
            tool_calls_str = tool_calls  # Use tool_calls directly since it's already a string
            print(f"DEBUG - Tool calls from run_test_case: {tool_calls_str}")
            print(f"DEBUG - Tool calls type: {type(tool_calls_str)}")
            print(f"DEBUG - Tool calls length: {len(str(tool_calls_str)) if tool_calls_str else 0}")
            # ---
            
            if not api_call_success:
                # API call failed - just mark as failed and log in history
                error_msg = "API call failed" if not response else str(response)
                run_manager.mark_test_failed(test_id, run_number, error_msg)
                
                # Add minimal information to test results for reporting
                test_result = {
                    "test_no": test_case["test_no"],
                    "run_number": run_number,
                    "query": query,
                    "ground_truth": test_case.get("ground_truth", ""),
                    "extracted_true_value": test_case.get("extracted_true_value"),
                    "response": str(response) if response else "API call failed",
                    "api_call_success": False,
                    "ragas_evaluated": False,
                    "token_usage": token_usage,
                    "tool_calls": tool_calls_str
                }
                all_test_results.append(test_result)
                continue
            
            # API call succeeded, run RAGAS evaluation
            ragas_success, ragas_result, ragas_error = evaluate_single_test(
                test_case,
                response,
                context,
                test_case["reference_contexts"],
                model_id
            )
            
            if not ragas_success:
                # RAGAS evaluation failed - mark as failed and log in history
                error_msg = f"RAGAS evaluation failed: {ragas_error}"
                run_manager.mark_test_failed(test_id, run_number, error_msg)
                
                # Add to results for reporting
                test_result = {
                    "test_no": test_case["test_no"],
                    "run_number": run_number,
                    "query": query,
                    "ground_truth": test_case.get("ground_truth", ""),
                    "extracted_true_value": test_case.get("extracted_true_value"),
                    "response": response,
                    "context": context,
                    "reference_contexts": test_case.get("reference_contexts", []),
                    "api_call_success": True,
                    "ragas_evaluated": False,
                    "ragas_error": ragas_error,
                    "token_usage": token_usage,
                    "tool_calls": tool_calls_str
                }
                all_test_results.append(test_result)
                continue
            
            # Everything succeeded - proceed to save to database
            try:
                # Process RAGAS metrics if available
                if ragas_success and ragas_result:
                    # Extract metrics from the RAGAS result
                    try:
                        # Based on the log output, ragas_result behaves like a dict 
                        # but is actually an EvaluationResult object
                        metrics = {}
                        
                        # Check if it has a _repr_dict with all metrics
                        if hasattr(ragas_result, '_repr_dict') and ragas_result._repr_dict:
                            metrics = ragas_result._repr_dict
                        # Fall back to using it as a dict directly
                        elif hasattr(ragas_result, '__getitem__'):
                            metrics = ragas_result
                        
                        # Add each metric to evaluation_data, properly handling 0 values
                        evaluation_data = {
                            "retrieved_contexts": str(test_case["reference_contexts"]),
                            "ground_truth": test_case["ground_truth"],
                        }
                        evaluation_data["factual_correctness"] = metrics.get("lenient_factual_correctness")
                        evaluation_data["semantic_similarity"] = metrics.get("semantic_similarity")
                        evaluation_data["context_recall"] = metrics.get("context_recall")
                        evaluation_data["faithfulness"] = metrics.get("faithfulness")
                        evaluation_data["bleu_score"] = metrics.get("bleu_score")
                        evaluation_data["non_llm_string_similarity"] = metrics.get("non_llm_string_similarity")
                        evaluation_data["rogue_score"] = metrics.get("rouge_score(mode=fmeasure)") or metrics.get("rouge_score")
                        evaluation_data["string_present"] = metrics.get("string_present")
                        
                        # Save the results to database immediately for this test
                        query_eval_id = save_query_with_eval_to_db(
                            query=query,
                            direct_response=response,
                            full_response=context,
                            llm_model_id=model_id,
                            evaluation_results=evaluation_data,
                            sql_queries=[],  # We can add SQL extraction if needed
                            token_usage=token_usage,
                            test_no=test_case.get("test_no"),
                            tool_calls=tool_calls_str
                        )
                        
                        # Mark the test as successful
                        run_manager.mark_test_success(test_id, run_number, query_eval_id)
                        
                    except Exception as e:
                        logger.error(f"Failed to process RAGAS metrics: {e}")
                        print(f"Failed to process RAGAS metrics: {e}")
                        # Make sure evaluation_data exists even on failure
                        if 'evaluation_data' not in locals():
                            evaluation_data = {
                                "retrieved_contexts": str(test_case["reference_contexts"]),
                                "ground_truth": test_case["ground_truth"],
                            }
                        # Ensure query_eval_id is set to None if the RAGAS processing fails
                        query_eval_id = None
                        # Mark the test as failed
                        run_manager.mark_test_failed(test_id, run_number, f"RAGAS processing error: {e}")
                
                # Create test result with all the metrics included
                test_result = {
                    "test_no": test_case["test_no"],
                    "run_number": run_number,
                    "query": query,
                    "ground_truth": test_case["ground_truth"],
                    "extracted_true_value": test_case.get("extracted_true_value"),
                    "response": response,
                    "context": context,
                    "reference_contexts": test_case["reference_contexts"],
                    "api_call_success": True,
                    "ragas_evaluated": ragas_success,
                    "token_usage": token_usage,
                    "query_evaluation_id": query_eval_id,  # Now we include this since we saved to DB
                    "tool_calls": tool_calls_str,
                    
                    # Include all individual metrics for reporting
                    "factual_correctness": evaluation_data.get("factual_correctness"),
                    "semantic_similarity": evaluation_data.get("semantic_similarity"),
                    "context_recall": evaluation_data.get("context_recall"),
                    "faithfulness": evaluation_data.get("faithfulness"),
                    "bleu_score": evaluation_data.get("bleu_score"),
                    "non_llm_string_similarity": evaluation_data.get("non_llm_string_similarity"),
                    "rogue_score": evaluation_data.get("rogue_score"),
                    "string_present": evaluation_data.get("string_present")
                }
                
                # Instead of storing the raw RAGAS result object, store only the metrics in a serializable format
                if ragas_success and ragas_result:
                    if hasattr(ragas_result, '_repr_dict'):
                        test_result["ragas_metrics"] = ragas_result._repr_dict
                    else:
                        test_result["ragas_metrics"] = str(ragas_result)
                else:
                    test_result["ragas_metrics"] = None
                
                all_test_results.append(test_result)
                all_ragas_results.append(ragas_result)
                run_manager.add_successful_evaluation(test_result)
                
            except Exception as e:
                logger.error(f"Failed to process RAGAS metrics: {e}")
                print(f"Failed to process RAGAS metrics: {e}")
                evaluation_data = {
                    "retrieved_contexts": str(test_case["reference_contexts"]),
                    "ground_truth": test_case["ground_truth"],
                }
                # Ensure query_eval_id is set to None if the RAGAS processing fails
                query_eval_id = None
                # Mark the test as failed
                run_manager.mark_test_failed(test_id, run_number, f"RAGAS processing error: {e}")
            
            # After the test completes successfully
            current_run += 1
            
            try:
                if has_app_context():
                    socketio.emit('evaluation_progress', {
                        'progress': current_run,
                        'total': total_runs,
                        'percent': int((current_run / total_runs) * 100),
                        'test_no': test_id,
                        'total_tests': total_tests,
                        'iteration': run_number,
                        'total_iterations': number_of_runs,
                        'message': f'Completed test {test_id}/{total_tests}, iteration {run_number}/{number_of_runs}'
                    }, namespace='/query')
                    # Add debug log to confirm emission
                    logger.info(f"Emitted progress update: Test {test_id}/{total_tests}, Iteration {run_number}/{number_of_runs}, Progress {current_run}/{total_runs}")
                else:
                    logger.info(f"Progress update (no socket context): Test {test_id}/{total_tests}, Iteration {run_number}/{number_of_runs}, Progress {current_run}/{total_runs}")
            except Exception as e:
                logger.error(f"Error emitting completion progress: {e}")
            
        except Exception as e:
            logger.error(f"Error running test {test_id} (run {run_number}): {e}")
            run_manager.mark_test_failed(test_id, run_number, str(e))
            
            # Small delay before retrying to avoid overwhelming the API
            time.sleep(1)
    
    # Final progress update
    if progress_callback:
        summary = run_manager.get_summary()
        progress_callback(
            summary["total_tests"],
            summary["total_tests"],
            f"Completed {summary['successful_tests']}/{summary['total_tests']} tests successfully"
        )
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(all_test_results) if all_test_results else None
    
    # Combine RAGAS results if available
    combined_ragas_results = None
    if all_ragas_results:
        # Logic to combine RAGAS results (similar to existing code)
        combined_ragas_results = all_ragas_results[0]
        # Additional logic for combining multiple results would go here
    
    # Generate summary
    summary = run_manager.get_summary()
    logger.info(f"Test run summary: {summary}")
    
    # Convert any non-serializable objects in combined_ragas_results
    serializable_combined_results = None
    if combined_ragas_results:
        if hasattr(combined_ragas_results, '_repr_dict'):
            serializable_combined_results = combined_ragas_results._repr_dict
        elif hasattr(combined_ragas_results, 'to_dict') and callable(combined_ragas_results.to_dict):
            serializable_combined_results = combined_ragas_results.to_dict()
        else:
            serializable_combined_results = str(combined_ragas_results)

    # Convert results_df to JSON-serializable format
    if results_df is not None:
        # Convert DataFrame to a dict of records for JSON serialization
        results_dict = results_df.to_dict(orient='records')
    else:
        results_dict = []

    # Create a complete, serializable results object
    final_results = {
        "summary": run_manager.get_summary(),
        "tests": results_dict,
        "combined_metrics": serializable_combined_results
    }

    # Convert results into a nicely formatted Markdown string and metrics object
    def format_test_results_for_response(test_results, combined_metrics):
        # Create a Markdown-formatted string for the full response
        markdown_output = "# Evaluation Results\n\n"
        
        for test in test_results:
            test_no = test.get("test_no", "Unknown")
            markdown_output += f"## Test Case {test_no}\n\n"
            
            # Question
            markdown_output += f"### Question\n{test.get('query', '')}\n\n"
            
            # Reference Answer
            markdown_output += f"### Reference Answer\n{test.get('ground_truth', '')}\n\n"
            
            # Model Response
            markdown_output += f"### Model Response\n{test.get('response', '')}\n\n"
            
            # Context
            markdown_output += f"### Context\n{test.get('context', [])}\n\n"
            
            markdown_output += "---\n\n"
        
        # Format the metrics for the results object
        results = {}
        if combined_metrics:
            # Map the metrics to the expected format
            results = {
                "bleu_score": combined_metrics.get("bleu_score", 0),
                "context_recall": combined_metrics.get("context_recall", 0),
                "faithfulness": combined_metrics.get("faithfulness", 0),
                "lenient_factual_correctness": combined_metrics.get("lenient_factual_correctness", 0),
                "non_llm_string_similarity": round(combined_metrics.get("non_llm_string_similarity", 0), 4),
                "rouge_score(mode=fmeasure)": round(combined_metrics.get("rouge_score(mode=fmeasure)", 0), 4),
                "semantic_similarity": round(combined_metrics.get("semantic_similarity", 0), 4),
                "string_present": combined_metrics.get("string_present", 0)
            }
        
        return {
            "full_response": markdown_output,
            "results": results
        }

    # Convert results_df to a list of dictionaries if it's not None
    results_dict = results_df.to_dict(orient='records') if results_df is not None else []

    # Format the response in the required structure
    formatted_response = format_test_results_for_response(results_dict, serializable_combined_results)

    return combined_ragas_results, results_df

def update_progress(progress, total, message, test_no=None, total_tests=None, iteration=None, total_iterations=None):
    """Update progress via WebSocket"""
    try:
        if has_app_context():
            socketio.emit('evaluation_progress', {
                'progress': progress,
                'total': total,
                'percent': int((progress / total) * 100) if total > 0 else 0,
                'message': message,
                'test_no': test_no if test_no is not None else progress,
                'total_tests': total_tests if total_tests is not None else total,
                'iteration': iteration if iteration is not None else 0,
                'total_iterations': total_iterations if total_iterations is not None else 1
            }, namespace='/query')
        else:
            logger.info(f"Progress update (no socket context): {message}")
    except Exception as e:
        logger.error(f"Error emitting progress update: {e}")