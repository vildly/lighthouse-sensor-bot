import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import time
from enum import Enum
from app.conf.postgres import get_cursor

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

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
        Get the next pending test case to run.
        
        Returns:
            Tuple of (test_id, run_number, test_case) or None if no pending tests
        """
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                if run_info["status"] == TestStatus.PENDING:
                    logger.debug(f"Selected pending test {test_id} run {run_number}")
                    return test_id, run_number, run_info["test_case"]
        
        # If no pending tests, look for failed tests that can be retried
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                if (run_info["status"] == TestStatus.FAILED and 
                    run_info["retry_count"] < self.max_retries):
                    logger.debug(f"Selected failed test {test_id} run {run_number} for retry (attempt {run_info['retry_count'] + 1})")
                    return test_id, run_number, run_info["test_case"]
        
        logger.info("No more pending or retriable tests found")
        return None
    
    def mark_test_running(self, test_id: str, run_number: int) -> None:
        """Mark a test as running"""
        if test_id in self.test_status and run_number in self.test_status[test_id]:
            prev_status = self.test_status[test_id][run_number]["status"]
            retry_count = self.test_status[test_id][run_number]["retry_count"]
            
            self.test_status[test_id][run_number]["status"] = TestStatus.RUNNING
            
            logger.info(f"Test {test_id} run {run_number} status change: {prev_status.value} -> RUNNING (retry {retry_count})")
            self._log_test_status_summary()
    
    def mark_test_success(self, test_id: str, run_number: int, 
                         query_evaluation_id: Optional[int] = None) -> None:
        """Mark a test as successful and record in history"""
        if test_id in self.test_status and run_number in self.test_status[test_id]:
            run_info = self.test_status[test_id][run_number]
            prev_status = run_info["status"]
            run_info["status"] = TestStatus.SUCCESS
            
            # Record success in database
            retry_count = run_info["retry_count"]
            self._record_attempt_history(
                test_id, run_number, retry_count, "success", 
                query_evaluation_id=query_evaluation_id
            )
            
            logger.info(f"Test {test_id} run {run_number} status change: {prev_status.value} -> SUCCESS (retry {retry_count}, query_eval_id: {query_evaluation_id})")
            self._log_test_status_summary()
    
    def mark_test_failed(self, test_id: str, run_number: int, error_message: str) -> None:
        """Mark a test as failed, increment retry count, and record in history"""
        if test_id in self.test_status and run_number in self.test_status[test_id]:
            run_info = self.test_status[test_id][run_number]
            prev_status = run_info["status"]
            prev_retry = run_info["retry_count"]
            
            run_info["status"] = TestStatus.FAILED
            run_info["retry_count"] += 1
            current_retry = run_info["retry_count"]
            
            # Record failure in database
            self._record_attempt_history(
                test_id, run_number, prev_retry, 
                "failed", error_message=error_message
            )
            
            logger.info(f"Test {test_id} run {run_number} status change: {prev_status.value} -> FAILED (retry {prev_retry} -> {current_retry})")
            
            # Check if we've exceeded max retries
            if current_retry >= self.max_retries:
                logger.warning(
                    f"Test {test_id} run {run_number} has failed {self.max_retries} times, "
                    f"will not retry again. Last error: {error_message[:100]}..."
                )
            else:
                # Set back to pending for retry
                run_info["status"] = TestStatus.PENDING
                logger.info(
                    f"Test {test_id} run {run_number} marked for retry "
                    f"(attempt {current_retry})"
                )
            
            self._log_test_status_summary()
    
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
    
    def all_tests_completed(self) -> bool:
        """Check if all tests have been completed successfully or failed permanently"""
        incomplete_tests = []
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                # Test is incomplete if it's pending or running
                if run_info["status"] in [TestStatus.PENDING, TestStatus.RUNNING]:
                    incomplete_tests.append((test_id, run_number, run_info["status"].value))
                    continue
                
                # Test is incomplete if it failed but has retries left
                if (run_info["status"] == TestStatus.FAILED and 
                    run_info["retry_count"] < self.max_retries):
                    incomplete_tests.append((test_id, run_number, f"{run_info['status'].value} (retry {run_info['retry_count']})"))
                    continue
        
        if incomplete_tests:
            logger.debug(f"Incomplete tests: {incomplete_tests}")
            return False
        
        logger.info("All tests have been completed!")
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of test run status"""
        total_tests = len(self.test_status) * self.number_of_runs
        successful_tests = 0
        failed_tests = 0
        pending_tests = 0
        running_tests = 0
        
        for test_id, runs in self.test_status.items():
            for run_number, run_info in runs.items():
                if run_info["status"] == TestStatus.SUCCESS:
                    successful_tests += 1
                elif run_info["status"] == TestStatus.FAILED and run_info["retry_count"] >= self.max_retries:
                    failed_tests += 1
                elif run_info["status"] == TestStatus.PENDING:
                    pending_tests += 1
                elif run_info["status"] == TestStatus.RUNNING:
                    running_tests += 1
        
        summary = {
            "model_id": self.model_id,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "pending_tests": pending_tests,
            "running_tests": running_tests,
            "completion_percentage": (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        logger.info(f"Test run summary: {summary}")
        return summary
    
    def add_successful_evaluation(self, evaluation_data: Dict[str, Any]) -> None:
        """Add a successful evaluation to the list for reporting"""
        self.successful_evaluations.append(evaluation_data)
        logger.debug(f"Added successful evaluation for test {evaluation_data.get('test_no')}, run {evaluation_data.get('run_number')}")
    
    def get_successful_evaluations(self) -> List[Dict[str, Any]]:
        """Get all successful evaluations"""
        return self.successful_evaluations


def execute_test_runs(model_id: str, number_of_runs: int = 1, 
                     max_retries: int = 3, progress_callback=None):
    """
    Main function to execute all test runs with retry logic.
    
    Args:
        model_id: The model ID to test
        number_of_runs: Number of successful runs needed for each test
        max_retries: Maximum retry attempts per test
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Tuple of (combined_ragas_results, all_tests_df)
    """
    from app.ragas.scripts.synthetic_ragas_tests import (
        load_synthetic_test_cases, 
        run_test_case, 
        evaluate_single_test
    )
    from app.helpers.save_query_to_db import save_query_with_eval_to_db
    import pandas as pd
    
    # Load test cases
    test_cases = load_synthetic_test_cases()
    if not test_cases:
        logger.error("No test cases loaded")
        return None, None
    
    # Initialize test run manager
    run_manager = TestRunManager(model_id, number_of_runs, max_retries)
    run_manager.initialize_test_runs(test_cases)
    
    # Execute test runs until all are completed
    all_test_results = []
    all_ragas_results = []
    
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
            progress_callback(
                summary["successful_tests"] + summary["failed_tests"],
                summary["total_tests"],
                f"Running test {test_id} (run {run_number}/{number_of_runs})"
            )
        
        # Mark test as running
        run_manager.mark_test_running(test_id, run_number)
        
        try:
            logger.info(f"Running test {test_id} (run {run_number}/{number_of_runs})")
            
            # Run the test case
            query = test_case["query"]
            response, context, api_call_success, token_usage = run_test_case(
                query, model_id, test_case.get("test_no")
            )
            
            if not api_call_success:
                # API call failed
                error_msg = "API call failed" if not response else str(response)
                run_manager.mark_test_failed(test_id, run_number, error_msg)
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
                # RAGAS evaluation failed
                run_manager.mark_test_failed(
                    test_id, run_number, f"RAGAS evaluation failed: {ragas_error}"
                )
                continue
            
            # Everything succeeded - save to database
            query_eval_id = None
            try:
                # Create evaluation results dictionary for saving to database
                evaluation_data = {
                    "retrieved_contexts": str(test_case["reference_contexts"]),
                    "ground_truth": test_case["ground_truth"],
                }
                
                # Extract metrics from RAGAS result
                if isinstance(ragas_result, dict):
                    metrics = ragas_result
                elif hasattr(ragas_result, '__dict__'):
                    metrics = ragas_result.__dict__
                elif hasattr(ragas_result, 'to_dict'):
                    metrics = ragas_result.to_dict()
                else:
                    metrics = {}
                
                # Map to our expected metric names
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
                
                for ragas_key, our_key in metric_mapping.items():
                    value = metrics.get(ragas_key)
                    evaluation_data[our_key] = value
                
                # Save to database and get the query evaluation ID
                query_eval_id = save_query_with_eval_to_db(
                    query=query,
                    direct_response=response,
                    full_response=context,
                    llm_model_id=model_id,
                    evaluation_results=evaluation_data,
                    token_usage=token_usage
                )
                
                logger.info(f"Saved to database with query_evaluation_id: {query_eval_id}")
            except Exception as save_error:
                logger.error(f"Error saving to database: {save_error}")
            
            # Mark test as successful with the query evaluation ID
            run_manager.mark_test_success(test_id, run_number, query_eval_id)
            
            # Add to results
            test_result = {
                "test_no": test_case["test_no"],
                "run_number": run_number,
                "query": query,
                "ground_truth": test_case["ground_truth"],
                "response": response,
                "context": context,
                "reference_contexts": test_case["reference_contexts"],
                "api_call_success": True,
                "ragas_evaluated": True,
                "ragas_results": ragas_result,
                "token_usage": token_usage,
                "query_evaluation_id": query_eval_id
            }
            
            all_test_results.append(test_result)
            all_ragas_results.append(ragas_result)
            run_manager.add_successful_evaluation(test_result)
            
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
    
    return combined_ragas_results, results_df 