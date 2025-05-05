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
            # Update the experiment_runs table
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

            # Only record in run_attempt_history if we have a query_evaluation_id or it's not a success status
            # This prevents duplicate entries for successful runs
            if status != 'success' or query_evaluation_id is not None:
                try:
                    history_sql = """
                    INSERT INTO run_attempt_history 
                    (model_id, test_case_id, run_number, attempt_timestamp, attempt_status, error_message, query_evaluation_id)
                    VALUES (%s, %s, %s, NOW(), %s, %s, %s)
                    """
                    cursor.execute(history_sql, (model_id, test_case_id, run_number, status, error_message, query_evaluation_id))
                except Exception as e:
                    logger.error(f"Error recording attempt history: {e}")

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
            ORDER BY last_attempt_timestamp ASC
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

def retry_failed_experiment_runs(batch_size=5, max_retries=3, wait_time=10, filter_model=None):
    """Retry failed experiment runs up to a maximum number of retries."""
    logger.info(f"Starting retry process: batch_size={batch_size}, max_retries={max_retries}, wait_time={wait_time}")
    
    total_processed = 0
    total_retried_successfully = 0
    
    while True:
        # Get a batch of failed runs
        failed_runs_data = get_failed_runs_for_retry(batch_size, max_retries, filter_model)
        
        if not failed_runs_data:
            logger.info("No more failed runs eligible for retry.")
            break
            
        logger.info(f"Found {len(failed_runs_data)} runs to retry in this batch.")
        
        for run_data in failed_runs_data:
            model_id, test_case_id, run_number, current_retry_count = run_data
            next_retry = (current_retry_count or 0) + 1
            
            logger.info(f"Retrying: Model={model_id}, Test={test_case_id}, Run={run_number}, Attempt={next_retry}/{max_retries}")
            
            # Mark as running
            mark_run_as_running(model_id=model_id, test_case_id=test_case_id, run_number=run_number)
            
            final_status = 'failed' # Default to failed unless confirmed success
            error_msg_for_update = f"Retry attempt {next_retry} did not result in success."
            from app.services.query_with_eval import query_with_eval

            try:
                # Call query_with_eval - it handles its own internal status updates per test case
                # We ignore the returned result/status code here as it reflects the whole batch
                query_with_eval(model_id, run_number) 
                
                # Check the ACTUAL status of THIS specific run after query_with_eval
                with get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT status, last_error FROM experiment_runs
                        WHERE model_id = %s AND test_case_id = %s AND run_number = %s
                        """,
                        (model_id, test_case_id, run_number)
                    )
                    result = cursor.fetchone()
                    if result:
                        final_status = result[0]
                        error_msg_for_update = result[1] # Use the error message from the last update
                        if final_status == 'success':
                            logger.info(f"✅ Successfully retried and processed Test={test_case_id}.")
                            total_retried_successfully += 1
                        else:
                             logger.warning(f"⚠️ Retry attempt {next_retry} for Test={test_case_id} finished with status: {final_status}.")
                    else:
                        logger.error(f"Could not find run {model_id}/{test_case_id}/{run_number} after retry attempt.")
                        final_status = 'failed' # Treat as failed if record disappears
                        error_msg_for_update = "Run record not found after retry attempt."

                # If the status is still failed after the attempt, ensure retry count is updated
                if final_status != 'success':
                    update_experiment_run_status(
                        model_id=model_id,
                        test_case_id=test_case_id,
                        run_number=run_number,
                        status='failed',
                        error_message=error_msg_for_update,
                        retry_count=next_retry
                    )

            except Exception as e:
                # Catch errors during the retry call itself (e.g., network issues calling query_with_eval)
                error_msg = f"Error during retry attempt {next_retry}: {str(e)[:500]}" # Truncate long errors
                logger.error(f"❌ {error_msg}")
                final_status = 'failed' # Ensure status is marked failed
                
                # Update experiment run status to failed with incremented retry count
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

def get_failed_runs_for_retry(batch_size=5, max_retries=3, filter_model=None):
    """Get a batch of failed experiments to retry that haven't reached max retry count"""
    try:
        with get_cursor() as cursor:
            query = """
            SELECT model_id, test_case_id, run_number, retry_count
            FROM experiment_runs
            WHERE status = 'failed'
            AND (retry_count IS NULL OR retry_count < %s)
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
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching failed experiments for retry: {e}")
        return []