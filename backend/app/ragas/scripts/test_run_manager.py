import logging
from app.conf.postgres import get_cursor
from typing import List, Dict, Optional, Callable, Tuple, Any
import time
import pandas as pd
import requests
import json
from datetime import datetime
from app.helpers.save_query_to_db import save_query_with_eval_to_db

logger = logging.getLogger(__name__)

def create_test_run(model_id, total_tests):
    """Create a new test run and return its ID"""
    try:
        with get_cursor() as cursor:
            # Get numeric model ID if string was provided
            if isinstance(model_id, str):
                cursor.execute("SELECT id FROM llm_models WHERE name = %s", (model_id,))
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Model {model_id} not found in llm_models table")
                    return None
                model_id = result[0]
                
            # Create test run record
            cursor.execute(
                """
                INSERT INTO test_runs (model_id, total_tests, status)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (model_id, total_tests, 'running')
            )
            test_run_id = cursor.fetchone()[0]
            return test_run_id
    except Exception as e:
        logger.error(f"Error creating test run: {e}")
        return None

def update_test_run_status(test_run_id, successful, api_failed, ragas_failed):
    """Update test run with completion status"""
    try:
        with get_cursor() as cursor:
            # Calculate total tests
            total = successful + api_failed + ragas_failed
            
            # Calculate success percentage
            success_percent = (successful / total) * 100 if total > 0 else 0
            
            cursor.execute(
                """
                UPDATE test_runs
                SET status = 'completed',
                    successful_tests = %s,
                    api_failed = %s,
                    ragas_failed = %s,
                    success_percent = %s,
                    completed_at = NOW()
                WHERE id = %s
                """,
                (successful, api_failed, ragas_failed, success_percent, test_run_id)
            )
            logger.info(f"Updated test run {test_run_id} status: {successful} successful, {api_failed} API failed, {ragas_failed} RAGAS failed")
            return True
    except Exception as e:
        logger.error(f"Error updating test run status: {e}")
        return False

def ensure_experiment_runs_populated(model_id, test_cases, num_runs=1):
    """Ensure experiment_runs table has entries for all test cases for this model"""
    if not test_cases:
        logger.error("No test cases provided to populate experiment runs")
        return 0
        
    try:
        with get_cursor() as cursor:
            # Get existing runs for this model to avoid duplicates
            cursor.execute(
                """
                SELECT test_case_id, run_number 
                FROM experiment_runs 
                WHERE model_id = %s
                """, 
                (model_id,)
            )
            existing_runs = set((row[0], row[1]) for row in cursor.fetchall())
            
            # Count how many we'll insert
            to_insert = []
            for test_case in test_cases:
                test_id = str(test_case.get('test_no', ''))
                if not test_id:
                    continue
                    
                for run_num in range(1, num_runs + 1):
                    if (test_id, run_num) not in existing_runs:
                        to_insert.append((model_id, test_id, run_num))
            
            # Bulk insert if we have any
            if to_insert:
                # Insert model_id, test_case_id, run_number. Status defaults to 'pending'.
                args = ','.join(cursor.mogrify("(%s,%s,%s)", row).decode('utf-8') for row in to_insert)
                cursor.execute(
                    f"""
                    INSERT INTO experiment_runs (model_id, test_case_id, run_number)
                    VALUES {args}
                    """
                )
                logger.info(f"Populated {len(to_insert)} experiment runs for model {model_id}")
            else:
                logger.info(f"No new experiment runs needed for model {model_id}")
                
            return len(to_insert)
    except Exception as e:
        logger.error(f"Error populating experiment runs: {e}")
        return 0

def update_experiment_run_status(model_id: str, test_case_id: str, run_number: int, 
                                 status: str, error_message: Optional[str] = None, 
                                 query_evaluation_id: Optional[int] = None,
                                 retry_count: Optional[int] = None):
    """Updates the status and error of an experiment run using get_cursor."""
    try:
        with get_cursor() as cursor:
            sql = """
            UPDATE experiment_runs
            SET status = %s,
                last_error = %s,
                last_attempt_timestamp = NOW()
            """
            params = [status, error_message]

            if retry_count is not None:
                sql += ", retry_count = %s"
                params.append(retry_count)

            sql += """
            WHERE model_id = %s AND test_case_id = %s AND run_number = %s
            """
            params.extend([model_id, test_case_id, run_number])

            cursor.execute(sql, tuple(params))
            
            if cursor.rowcount > 0:
                 logger.info(f"Updated run: Model={model_id}, Test={test_case_id}, Run={run_number} to Status='{status}', RetryCount={retry_count}")
            else:
                 logger.warning(f"Could not find run to update: Model={model_id}, Test={test_case_id}, Run={run_number}")

    except Exception as e:
        logger.error(f"Error updating experiment run status: {e}")

def mark_run_as_running(model_id: str, test_case_id: str, run_number: int):
    """Marks a specific experiment run as 'running' using get_cursor."""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE experiment_runs
                SET status = 'running', last_attempt_timestamp = NOW()
                WHERE model_id = %s AND test_case_id = %s AND run_number = %s
                """,
                (model_id, test_case_id, run_number)
            )
            if cursor.rowcount > 0:
                logger.info(f"Marked run as running: Model={model_id}, Test={test_case_id}, Run={run_number}")
            else:
                 logger.warning(f"Could not find run to mark as running: Model={model_id}, Test={test_case_id}, Run={run_number}")
    except Exception as e:
        logger.error(f"Error marking run as running: {e}")

def get_pending_experiments(batch_size=5, filter_model=None):
    """Get a batch of pending experiments to process"""
    try:
        with get_cursor() as cursor:
            query = """
            SELECT model_id, test_case_id, run_number
            FROM experiment_runs
            WHERE status = 'pending'
            """
            
            params = []
            
            if filter_model:
                query += " AND model_id = %s"
                params.append(filter_model)
                
            query += """
            ORDER BY created_at ASC
            LIMIT %s
            """
            params.append(batch_size)
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching pending experiments: {e}")
        return []

def get_models():
    """Get list of available models"""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT name FROM llm_models ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return []

def run_batch_experiments(batch_size=5, wait_time=5, max_retries=3, filter_model=None):
    """Run batch experiments from the experiment_runs table"""
    from app.services.query_with_eval import query_with_eval

    total_processed = 0
    retries = 0

    logger.info(f"Starting initial batch run with batch size: {batch_size}")

    # --- Initial Processing Loop ---
    while total_processed < batch_size and retries < max_retries:
        # Get pending experiments
        pending_runs = get_pending_experiments(batch_size, filter_model)

        if not pending_runs:
            logger.info("No pending experiments found in initial run.")
            retries += 1
            time.sleep(wait_time)
            continue

        retries = 0  # Reset retries when we find pending experiments
        logger.info(f"Found {len(pending_runs)} pending experiments for initial processing")

        for model_id, test_case_id, run_number in pending_runs:
            logger.info(f"Running initial experiment: Model={model_id}, Test={test_case_id}, Run={run_number}")

            # Mark as running
            mark_run_as_running(model_id, test_case_id, run_number)

            try:
                # Run the evaluation
                result, status_code = query_with_eval(model_id, run_number)

                # Log completion
                if status_code == 200:
                    logger.info(f"✅ Initial experiment completed successfully")
                    # Update status to success
                    update_experiment_run_status(model_id, test_case_id, run_number, 'success')
                else:
                    logger.warning(f"⚠️ Initial experiment returned status code: {status_code}")
                    # Update status to failed
                    update_experiment_run_status(
                        model_id,
                        test_case_id,
                        run_number,
                        'failed',
                        f"API returned status code: {status_code}"
                    )

                total_processed += 1

            except Exception as e:
                logger.error(f"❌ Error running initial experiment: {e}")
                # Update status to failed
                update_experiment_run_status(
                    model_id,
                    test_case_id,
                    run_number,
                    'failed',
                    str(e)
                )

        # Wait before processing next batch (if any more pending runs exist within the initial batch size limit)
        if pending_runs and total_processed < batch_size:
            logger.info(f"Waiting {wait_time} seconds before next initial batch...")
            time.sleep(wait_time)
    # --- End Initial Processing Loop ---

    logger.info(f"Initial processing loop completed. Processed {total_processed} runs.")

    # --- Automatic Retry Phase ---
    logger.info("Initiating automatic retry phase for any failed runs...")
    # Call the function to automatically retry all failed runs until none are left
    # Use the same max_retries, batch_size, and wait_time for consistency, or adjust as needed
    total_retried = auto_retry_all_failed_runs(
        max_retries=max_retries,
        batch_size=batch_size,
        wait_time=wait_time
    )
    logger.info(f"Automatic retry phase completed. Retried {total_retried} runs.")
    # --- End Automatic Retry Phase ---

    # Return the total processed in the initial phase (or potentially combined total if needed)
    return total_processed

def display_experiment_status():
    """Display current status of all experiment runs"""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    model_id,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM experiment_runs
                GROUP BY model_id
                ORDER BY model_id
                """
            )
            results = cursor.fetchall()
            
            # Convert to DataFrame for nice display
            df = pd.DataFrame(results, columns=['Model', 'Total', 'Pending', 'Running', 'Success', 'Failed'])
            
            print("\nExperiment Status Summary:")
            print("=" * 80)
            print(df.to_string(index=False))
            print("=" * 80)
            
            # Get overall totals
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM experiment_runs
                """
            )
            totals = cursor.fetchone()
            
            print("\nOverall Progress:")
            total = totals[0]
            completed = totals[3] + totals[4]  # success + failed
            percent = (completed / total) * 100 if total > 0 else 0
            print(f"Completed: {completed}/{total} ({percent:.1f}%)")
            
    except Exception as e:
        logger.error(f"Error displaying experiment status: {e}")

def run_synthetic_evaluation(
    llm_model_id, 
    progress_callback: Optional[Callable] = None,
    run_number: int = 1
):
    """Run evaluation using the synthetic test cases"""
    logger.info(f"Starting run_synthetic_evaluation (run #{run_number})...")

    # Load synthetic test cases
    test_cases = load_synthetic_test_cases()
    logger.info(f"Loaded test cases: {test_cases is not None}")

    if test_cases is None:
        logger.error("No test cases loaded - returning None")
        return None, None

    # REMOVE the ensure_experiment_runs_populated call here
    # This is already handled in query_with_eval or the API endpoint
    # We shouldn't pass run_number as num_runs because it's not the total runs needed
    
    # Initialize counters
    successful = 0
    api_failed = 0
    ragas_failed = 0

def start_evaluation_run(model_id: str, number_of_runs: int = 1) -> Tuple[Dict[str, Any], int]:
    """
    Start evaluation run(s) for a model, handling both single and batch runs.
    
    Args:
        model_id: The ID of the model to evaluate
        number_of_runs: Number of runs to perform (default: 1)
        
    Returns:
        Results from the first run and status code
    """
    from app.ragas.scripts.synthetic_ragas_tests import load_synthetic_test_cases
    from app.services.query_with_eval import query_with_eval
    import threading
    
    # Load test cases 
    test_cases = load_synthetic_test_cases()
    
    # Populate experiment_runs table
    ensure_experiment_runs_populated(model_id, test_cases, num_runs=number_of_runs)
    
    # Run first evaluation synchronously and get results to return
    results, status_code = query_with_eval(model_id, run_number=1)
    
    # Automatically retry any failed runs from the first evaluation
    logger.info("Starting automatic retry for any failed runs from initial evaluation...")
    auto_retry_all_failed_runs(max_retries=3, batch_size=5, wait_time=3)
    
    # Start background thread for remaining runs if needed
    if number_of_runs > 1:
        def run_remaining():
            # Use the modified run_batch_experiments with result tracking
            run_batch_experiments_with_updates(
                batch_size=number_of_runs-1,  # Exclude the first run
                filter_model=model_id,
                initial_results=results  # Pass the initial results to append to
            )
            
            # After all runs complete, automatically retry any failed runs
            logger.info("Starting automatic retry for any failed runs from background processing...")
            auto_retry_all_failed_runs(max_retries=3, batch_size=5, wait_time=3)
            
        thread = threading.Thread(target=run_remaining)
        thread.daemon = True
        thread.start()
        
    return results, status_code

def run_batch_experiments_with_updates(batch_size=5, wait_time=5, max_retries=3, 
                                      filter_model: Optional[str] = None,
                                      initial_results: Optional[Dict] = None):
    """
    Run batch experiments with progress updates via websocket.
    Appends each new test result to the existing results.
    """
    from app.services.query_with_eval import query_with_eval
    from flask_socketio import emit
    from app.conf.websocket import socketio
    
    total_processed = 0
    retries = 0
    accumulated_results = initial_results or {"results": {}, "full_response": "# Evaluation Results\n\n"}
    
    logger.info(f"Starting batch run with batch size: {batch_size}")
    
    while total_processed < batch_size and retries < max_retries:
        # Get pending experiments
        pending_runs = get_pending_experiments(batch_size, filter_model)
        
        if not pending_runs:
            logger.info("No pending experiments found.")
            retries += 1
            time.sleep(wait_time)
            continue
        
        retries = 0  # Reset retries when we find pending experiments
        logger.info(f"Found {len(pending_runs)} pending experiments")
        
        for model_id, test_case_id, run_number in pending_runs:
            logger.info(f"Running experiment: Model={model_id}, Test={test_case_id}, Run={run_number}")
            
            # Mark as running
            mark_run_as_running(model_id, test_case_id, run_number)
            
            try:
                # Run the evaluation
                result, status_code = query_with_eval(model_id, run_number)
                
                # Log completion
                if status_code == 200:
                    logger.info(f"✅ Experiment completed successfully")
                    # Update status to success
                    update_experiment_run_status(model_id, test_case_id, run_number, 'success')
                    
                    # Update the accumulated results
                    if "results" in result and "results" in accumulated_results:
                        # Merge metric results - average with existing values
                        for metric, value in result["results"].items():
                            if metric in accumulated_results["results"]:
                                # Average the values
                                accumulated_results["results"][metric] = (
                                    accumulated_results["results"][metric] + value
                                ) / 2
                            else:
                                accumulated_results["results"][metric] = value
                    
                    # Append this test's results to the full response
                    if "full_response" in result:
                        # Extract just the last test case from the new result
                        new_test_content = extract_last_test(result["full_response"])
                        if new_test_content:
                            # Append it to the accumulated full response
                            accumulated_results["full_response"] += new_test_content
                    
                    # Emit updated results via websocket
                    try:
                        socketio.emit('evaluation_update', {
                            'updated_results': accumulated_results,
                            'run_number': run_number,
                            'status': 'success'
                        }, namespace='/query')
                    except Exception as e:
                        logger.error(f"Error emitting updated results: {e}")
                    
                else:
                    logger.warning(f"⚠️ Experiment returned status code: {status_code}")
                    # Update status to failed
                    update_experiment_run_status(
                        model_id, 
                        test_case_id, 
                        run_number, 
                        'failed', 
                        f"API returned status code: {status_code}"
                    )
                
                total_processed += 1
                
            except Exception as e:
                logger.error(f"❌ Error running experiment: {e}")
                # Update status to failed
                update_experiment_run_status(
                    model_id, 
                    test_case_id, 
                    run_number, 
                    'failed', 
                    str(e)
                )
        
        # Wait before processing next batch
        if pending_runs:
            logger.info(f"Waiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)
    
    return total_processed

def extract_last_test(full_response):
    """Extract the last test case from a full response markdown string"""
    import re
    
    # Look for the last test case section
    test_sections = re.split(r'## Test Case \d+', full_response)
    if len(test_sections) > 1:
        # Return the last section with its header
        return f"## Test Case {len(test_sections)}{test_sections[-1]}"
    return ""

def retry_failed_experiment_runs(batch_size=5, wait_time=5, max_retries=3, filter_model=None):
    """Retry failed experiment runs that haven't exceeded max retry attempts using get_cursor."""
    from app.ragas.scripts.synthetic_ragas_tests import run_test_case, evaluate_single_test, load_synthetic_test_cases
    
    logger.info(f"Starting retry process for failed experiment runs (Max Retries: {max_retries})...")
    
    # Load all test cases for lookup
    test_cases = load_synthetic_test_cases()
    if not test_cases:
        logger.error("Cannot proceed with retries: Failed to load synthetic test cases")
        return 0
        
    # Create lookup dictionary
    test_case_dict = {str(tc['test_no']): tc for tc in test_cases}
    
    total_processed = 0
    total_retried_successfully = 0
    
    while True:
        # Get failed runs to retry using get_cursor
        failed_runs_data = []
        try:
            with get_cursor() as cursor:
                query = """
                SELECT model_id, test_case_id, run_number, COALESCE(retry_count, 0) as retry_count
                FROM experiment_runs
                WHERE status = 'failed'
                AND COALESCE(retry_count, 0) < %s
                """
                params = [max_retries]
                
                if filter_model:
                    query += " AND model_id = %s"
                    params.append(filter_model)
                    
                query += """
                ORDER BY last_attempt_timestamp ASC NULLS FIRST
                LIMIT %s
                """
                params.append(batch_size)
                
                cursor.execute(query, tuple(params))
                # Fetch as dictionaries for easier access
                columns = [desc[0] for desc in cursor.description]
                failed_runs_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching failed experiments: {e}")
            break # Stop if we can't fetch runs

        if not failed_runs_data:
            logger.info("No more failed runs found to retry")
            break
            
        logger.info(f"Found {len(failed_runs_data)} failed runs to retry")
        
        for run_data in failed_runs_data:
            model_id = run_data['model_id']
            test_case_id = run_data['test_case_id']
            run_number = run_data['run_number']
            current_retry = run_data['retry_count']
            next_retry = current_retry + 1
            
            logger.info(f"Retrying: Model={model_id}, Test={test_case_id}, Run={run_number}, Attempt={next_retry}")
            
            # Get test case details
            test_case = test_case_dict.get(str(test_case_id))
            if not test_case:
                logger.error(f"Cannot find test case details for test_id={test_case_id}. Skipping retry.")
                update_experiment_run_status(
                    model_id=model_id, 
                    test_case_id=test_case_id, 
                    run_number=run_number, 
                    status='failed', 
                    error_message="Test case details not found.",
                    retry_count=next_retry # Increment retry count even if skipped
                )
                
                continue

            query = test_case.get('query')
            ground_truth = test_case.get('ground_truth')
            
            # Mark as running
            mark_run_as_running(model_id=model_id, test_case_id=test_case_id, run_number=run_number)
            
            try:
                # --- Execute the single test case ---
                agent_response, contexts, api_call_success, token_usage = run_test_case(
                    query=query, 
                    llm_model_id=model_id, 
                    test_no=test_case_id
                )
                # --- End Execute Test Case ---

                if api_call_success:
                    # --- Evaluate RAGAS ---
                    ragas_results = evaluate_single_test(agent_response, contexts, ground_truth)
                    # --- End Evaluate RAGAS ---

                    # --- Save Results ---
                    query_eval_id = save_query_with_eval_to_db(
                        query=query, 
                        response=agent_response, 
                        contexts=contexts, 
                        evaluation_results=ragas_results, 
                        model_id=model_id, 
                        token_usage=token_usage,
                        test_case_id=test_case_id
                    )
                    # --- End Saving Results ---

                    # --- Record successful attempt in run_attempt_history ---
                    try:
                        with get_cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO run_attempt_history 
                                (model_id, test_case_id, run_number, attempt_timestamp, status, query_evaluation_id)
                                VALUES (%s, %s, %s, NOW(), %s, %s)
                                """,
                                (model_id, test_case_id, run_number, 'success', query_eval_id)
                            )
                    except Exception as e:
                        logger.error(f"Error recording successful attempt history: {e}")
                    # --- End Recording History ---

                    # --- Update ExperimentRun status to success ---
                    update_experiment_run_status(
                        model_id=model_id, 
                        test_case_id=test_case_id, 
                        run_number=run_number, 
                        status='success', 
                        error_message=None,
                        retry_count=next_retry # Record the successful retry attempt number
                    )
                    total_retried_successfully += 1
                    logger.info(f"✅ Successfully retried and processed Test={test_case_id}.")
                    # --- End Update Status ---

                else:
                    # API call failed again
                    error_msg = f"Retry attempt {next_retry} failed: API call error." 
                    logger.warning(f"⚠️ API call failed again for Test={test_case_id} on attempt {next_retry}.")
                    
                    # --- Record failed API attempt in run_attempt_history ---
                    try:
                        with get_cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO run_attempt_history 
                                (model_id, test_case_id, run_number, attempt_timestamp, status, error_message)
                                VALUES (%s, %s, %s, NOW(), %s, %s)
                                """,
                                (model_id, test_case_id, run_number, 'failed', error_msg)
                            )
                    except Exception as e:
                        logger.error(f"Error recording failed API attempt history: {e}")
                    # --- End Recording History ---
                    
                    update_experiment_run_status(
                        model_id=model_id, 
                        test_case_id=test_case_id, 
                        run_number=run_number, 
                        status='failed', 
                        error_message=error_msg,
                        retry_count=next_retry
                    )

            except Exception as e:
                # Catch errors during run_test_case, evaluation, or saving
                error_msg = f"Error during retry attempt {next_retry}: {str(e)[:500]}" # Truncate long errors
                logger.error(f"❌ {error_msg}")
                
                # --- Record error attempt in run_attempt_history ---
                try:
                    with get_cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO run_attempt_history 
                            (model_id, test_case_id, run_number, attempt_timestamp, status, error_message)
                            VALUES (%s, %s, %s, NOW(), %s, %s)
                            """,
                            (model_id, test_case_id, run_number, 'failed', error_msg)
                        )
                except Exception as hist_err:
                    logger.error(f"Error recording error attempt history: {hist_err}")
                # --- End Recording History ---
                
                update_experiment_run_status(
                    model_id=model_id, 
                    test_case_id=test_case_id, 
                    run_number=run_number, 
                    status='failed', 
                    error_message=error_msg,
                    retry_count=next_retry
                )
            
            total_processed += 1
            
        # Wait between batches if we processed a full batch
        if len(failed_runs_data) == batch_size:
            logger.info(f"Waiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)
        else:
            # If we processed less than a full batch, we're done
            break
    
    logger.info(f"Retry process finished. Total runs processed: {total_processed}, Successfully retried: {total_retried_successfully}")
    return total_processed

def auto_retry_all_failed_runs(max_retries=3, batch_size=5, wait_time=5):
    """
    Automatically retry all failed experiment runs until there are no more failed runs
    or until all runs have reached the maximum retry count.
    
    Args:
        max_retries: Maximum number of retry attempts per run
        batch_size: Number of runs to process in each batch
        wait_time: Seconds to wait between batches
        
    Returns:
        Total number of runs processed during retries
    """
    logger.info("Starting automatic retry of ALL failed experiment runs...")
    
    total_processed_retries = 0
    total_batches = 0
    
    while True:
        # Run a batch of retries using the existing retry function
        processed_in_batch = retry_failed_experiment_runs(
            batch_size=batch_size,
            wait_time=wait_time,
            max_retries=max_retries
        )
        
        # If no runs were processed in this batch, we're done
        if processed_in_batch == 0:
            logger.info("No more failed runs to retry - all runs have either succeeded or reached max retries")
            break
            
        total_processed_retries += processed_in_batch
        total_batches += 1
        
        logger.info(f"Completed retry batch {total_batches}, processed {processed_in_batch} runs in this batch")
        
        # Optional: Add a small delay between full retry cycles if needed
        # time.sleep(1) 
    
    logger.info(f"Auto-retry completed. Total runs processed across {total_batches} retry batches: {total_processed_retries}")
    return total_processed_retries