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
                        # Initialize with retry_count 0
                        to_insert.append((model_id, test_id, run_num, 0)) 
            
            # Bulk insert if we have any
            if to_insert:
                # Insert model_id, test_case_id, run_number, retry_count. Status defaults to 'pending'.
                args = ','.join(cursor.mogrify("(%s,%s,%s,%s)", row).decode('utf-8') for row in to_insert)
                cursor.execute(
                    f"""
                    INSERT INTO experiment_runs (model_id, test_case_id, run_number, retry_count)
                    VALUES {args}
                    ON CONFLICT (model_id, test_case_id, run_number) DO NOTHING 
                    """
                )
                # Log the number actually inserted (cursor.rowcount might be useful if ON CONFLICT is hit often)
                logger.info(f"Populated/Ensured {len(to_insert)} experiment runs for model {model_id}")
            else:
                logger.info(f"No new experiment runs needed for model {model_id}")
                
            # Return the count of runs intended for insertion
            return len(to_insert) 
    except Exception as e:
        logger.error(f"Error populating experiment runs: {e}")
        return 0

def update_experiment_run_status(model_id: str, test_case_id: str, run_number: int,
                                 status: str, error_message: Optional[str] = None,
                                 query_evaluation_id: Optional[int] = None,
                                 retry_count: Optional[int] = None):
    """Updates the status and error of an experiment run and logs the attempt history reliably."""
    try:
        with get_cursor() as cursor:
            # --- Get current state BEFORE update ---
            cursor.execute(
                """
                SELECT status, retry_count FROM experiment_runs
                WHERE model_id = %s AND test_case_id = %s AND run_number = %s
                """,
                (model_id, test_case_id, run_number)
            )
            current = cursor.fetchone()
            current_status = current[0] if current else None
            # Treat NULL retry_count in DB as 0 for comparison
            current_retry_db = current[1] if current and current[1] is not None else 0 

            # --- Determine the retry count for THIS attempt ---
            # If retry_count is explicitly passed (usually for retries), use that.
            # Otherwise, assume it's the initial attempt (retry_count 0).
            attempt_retry_count = retry_count if retry_count is not None else 0

            # --- Check if an update to experiment_runs is actually needed ---
            should_update_run = (
                not current or  # Record doesn't exist yet
                current_status != status or
                # Only update retry_count if explicitly passed and different from DB
                (retry_count is not None and retry_count != current_retry_db) 
            )

            update_succeeded = False
            if should_update_run:
                # --- Perform the UPDATE on experiment_runs ---
                sql = """
                UPDATE experiment_runs
                SET status = %s,
                    last_error = %s,
                    last_attempt_timestamp = NOW()
                """
                params = [status, error_message]

                # Only include retry_count in UPDATE if it's explicitly provided
                if retry_count is not None:
                    sql += ", retry_count = %s"
                    params.append(retry_count)
                
                sql += """
                WHERE model_id = %s AND test_case_id = %s AND run_number = %s
                """
                params.extend([model_id, test_case_id, run_number])

                cursor.execute(sql, tuple(params))
                update_succeeded = cursor.rowcount > 0

                if update_succeeded:
                    logger.info(f"Updated run: Model={model_id}, Test={test_case_id}, Run={run_number} to Status='{status}', RetryCount={attempt_retry_count}")
                else:
                    # This case should be rare if should_update_run was true, maybe indicates a race condition or missing record
                    logger.warning(f"Update condition met but no rows updated for run: Model={model_id}, Test={test_case_id}, Run={run_number}")
            else:
                logger.info(f"Skipping redundant update for Model={model_id}, Test={test_case_id}, Run={run_number} (Status: {status}, Retry: {retry_count})")
                # Even if the run wasn't updated (e.g., status already 'failed'), we might still need to log history if it wasn't logged before for this attempt
                update_succeeded = True # Allow history logging attempt even if run wasn't updated

            # --- Log attempt history using ON CONFLICT ---
            # Log if the update succeeded OR if we skipped the update but might still need to log history
            # Only log terminal states (success/failed) or if query_evaluation_id is present.
            if update_succeeded and (status in ['success', 'failed'] or query_evaluation_id is not None):
                try:
                    # Use INSERT ... ON CONFLICT DO NOTHING based on the unique constraint
                    # (model_id, test_case_id, run_number, retry_count)
                    history_sql = """
                    INSERT INTO run_attempt_history
                    (model_id, test_case_id, run_number, attempt_timestamp, attempt_status, error_message, query_evaluation_id, retry_count)
                    VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
                    ON CONFLICT (model_id, test_case_id, run_number, retry_count) DO NOTHING
                    """
                    cursor.execute(history_sql, (model_id, test_case_id, run_number, status, error_message, query_evaluation_id, attempt_retry_count))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Recorded attempt in history: Model={model_id}, Test={test_case_id}, Run={run_number}, Retry={attempt_retry_count}, Status={status}")
                    # else: # No warning needed, ON CONFLICT handled it.
                    #    logger.info(f"Attempt already recorded in history: Model={model_id}, Test={test_case_id}, Run={run_number}, Retry={attempt_retry_count}")

                except Exception as e:
                    # Catch potential errors during history insertion
                    logger.error(f"Error recording attempt history (Retry={attempt_retry_count}): {e}")

    except Exception as e:
        logger.error(f"Error updating experiment run status: {e}")

def mark_run_as_running(model_id: str, test_case_id: str, run_number: int):
     """DEPRECATED: Use update_experiment_run_status directly."""
     logger.warning("mark_run_as_running is deprecated. Use update_experiment_run_status.")
     # Optionally, call the main function for backward compatibility during transition:
     # update_experiment_run_status(model_id, test_case_id, run_number, 'running', 'Marked as running')
     pass # Or raise an error, or remove calls to it

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

def retry_failed_experiment_runs(filter_model: Optional[str] = None, batch_size: int = 5, max_retries: int = 3, wait_time: int = 60):
    """
    Retries failed experiment runs that haven't reached the maximum retry count.
    """
    logger.info(f"Starting auto-retry process. Max Retries={max_retries}, Batch Size={batch_size}, Wait Time={wait_time}s")
    
    total_processed_retries = 0
    total_batches = 0

    # Import necessary functions locally if needed, or ensure they are available in the scope
    from app.services.query_with_eval import query_with_eval 

    while True:
        # Get a batch of failed runs eligible for retry
        failed_runs_data = get_failed_runs_for_retry(
            batch_size=batch_size, 
            max_retries=max_retries, 
            filter_model=filter_model
        )
        
        if not failed_runs_data:
            logger.info("No more failed runs eligible for retry.")
            break
            
        logger.info(f"Found {len(failed_runs_data)} runs to retry in this batch.")
        processed_in_batch = 0

        for run_data in failed_runs_data:
            model_id, test_case_id, run_number, current_retry_count = run_data
            # current_retry_count from DB can be None, default to 0
            current_retry_count = current_retry_count if current_retry_count is not None else 0
            next_retry = current_retry_count + 1
            
            logger.info(f"Retrying: Model={model_id}, Test={test_case_id}, Run={run_number}, Attempt={next_retry}/{max_retries}")
            
            # Mark as running - IMPORTANT: Pass the next_retry count here!
            # This ensures the retry_count is updated BEFORE query_with_eval runs
            # and prevents race conditions where query_with_eval might log with the old count.
            update_experiment_run_status(
                model_id=model_id, 
                test_case_id=test_case_id, 
                run_number=run_number, 
                status='running', 
                error_message=f'Starting retry attempt {next_retry}', 
                retry_count=next_retry # Explicitly set the retry count for this attempt
            )
            
            try:
                # Call query_with_eval - it handles its own internal status updates per test case
                # It will call update_experiment_run_status with the correct retry_count (next_retry)
                # because we just updated it above.
                query_with_eval(model_id, run_number) 
                
                # After query_with_eval completes, check the final status recorded by it.
                # No need to call update_experiment_run_status again here, 
                # as query_with_eval should have already set the final status ('success' or 'failed')
                # and logged the history for attempt 'next_retry'.
                with get_cursor() as cursor:
                     cursor.execute(
                         """
                         SELECT status FROM experiment_runs
                         WHERE model_id = %s AND test_case_id = %s AND run_number = %s
                         """,
                         (model_id, test_case_id, run_number)
                     )
                     result = cursor.fetchone()
                     final_status = result[0] if result else 'unknown'
                     logger.info(f"Retry attempt {next_retry} for Run={run_number} completed with final status: {final_status}")
                     if final_status == 'success':
                         # Optional: track successful retries if needed
                         pass

            except Exception as e:
                logger.error(f"Unexpected error during retry attempt {next_retry} for run {model_id}/{test_case_id}/{run_number}: {e}")
                # Mark as failed if the retry process itself crashed
                # Ensure we pass the correct retry_count for this attempt
                update_experiment_run_status(
                    model_id=model_id, 
                    test_case_id=test_case_id, 
                    run_number=run_number, 
                    status='failed', 
                    error_message=f"Error during retry attempt {next_retry}: {str(e)}", 
                    retry_count=next_retry # Log failure against this attempt number
                )
            
            processed_in_batch += 1
            
            # Optional: Add delay between individual retries within a batch
            # time.sleep(1) 

        # If no runs were processed in this batch (e.g., all failed eligibility check), break
        if processed_in_batch == 0:
             logger.warning("Processed 0 runs in the current batch, exiting retry loop.")
             break
            
        total_processed_retries += processed_in_batch
        total_batches += 1
        
        logger.info(f"Completed retry batch {total_batches}, processed {processed_in_batch} runs in this batch")
        
        # Optional: Add a delay between full retry cycles
        # time.sleep(wait_time) 
    
    logger.info(f"Auto-retry completed. Total runs processed across {total_batches} retry batches: {total_processed_retries}")
    return total_processed_retries

def get_failed_runs_for_retry(batch_size=5, max_retries=3, filter_model=None):
    """Get a batch of failed experiments to retry that haven't reached max retry count"""
    try:
        with get_cursor() as cursor:
            params = [max_retries]
            query = """
            SELECT model_id, test_case_id, run_number, retry_count
            FROM experiment_runs
            WHERE status = 'failed'
            AND COALESCE(retry_count, 0) < %s 
            """ # Use COALESCE to treat NULL retry_count as 0

            if filter_model:
                query += " AND model_id = %s"
                params.append(filter_model)

            query += """
            ORDER BY last_attempt_timestamp ASC -- Retry oldest failures first
            LIMIT %s
            """
            params.append(batch_size)

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching failed runs for retry: {e}")
        return []

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