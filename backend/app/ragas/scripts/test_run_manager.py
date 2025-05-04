import logging
from app.conf.postgres import get_cursor
from typing import List, Dict, Optional, Callable, Tuple, Any
import time
import pandas as pd

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
            cursor.execute(
                """
                UPDATE test_runs
                SET status = %s,
                    successful_tests = %s,
                    failed_api_tests = %s,
                    failed_ragas_tests = %s,
                    completed_at = NOW()
                WHERE id = %s
                """,
                ('completed', successful, api_failed, ragas_failed, test_run_id)
            )
        return True
    except Exception as e:
        logger.error(f"Error updating test run status: {e}")
        return False

def ensure_experiment_runs_populated(model_id: str, test_cases: List[Dict], num_runs: int = 10):
    """Ensure experiment_runs table is populated with all required test runs"""
    try:
        with get_cursor() as cursor:
            runs_to_insert = []
            for test_case in test_cases:
                test_id = str(test_case.get('test_no', ''))
                for i in range(1, num_runs + 1):
                    runs_to_insert.append((model_id, test_id, i))
            
            # Use a more efficient batch insert approach with UNNEST
            if runs_to_insert:
                # Extract the columns of data for UNNEST
                model_ids, test_ids, run_numbers = zip(*runs_to_insert)
                
                cursor.execute(
                    """
                    INSERT INTO experiment_runs (model_id, test_case_id, run_number)
                    SELECT m, t, r 
                    FROM UNNEST(%s::text[], %s::text[], %s::int[]) AS u(m, t, r)
                    ON CONFLICT (model_id, test_case_id, run_number) DO NOTHING;
                    """,
                    (list(model_ids), list(test_ids), list(run_numbers))
                )
            
            return True
    except Exception as e:
        logger.error(f"Error populating experiment_runs table: {e}")
        return False

def update_experiment_run_status(model_id: str, test_id: str, run_number: int, 
                                status: str, error_msg: Optional[str] = None):
    """Update status in experiment_runs and add entry to run_attempt_history"""
    try:
        with get_cursor() as cursor:
            # Update experiment_runs with latest status
            cursor.execute(
                """
                UPDATE experiment_runs
                SET status = %s, last_error = %s, last_attempt_timestamp = NOW()
                WHERE model_id = %s AND test_case_id = %s AND run_number = %s;
                """,
                (status, error_msg, model_id, test_id, run_number)
            )
            
            # Log attempt to history table
            cursor.execute(
                """
                INSERT INTO run_attempt_history
                (model_id, test_case_id, run_number, attempt_status, error_message)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (model_id, test_id, run_number, status, error_msg)
            )
            
            return True
    except Exception as e:
        logger.error(f"Error updating experiment run status: {e}")
        return False

def get_pending_experiments(batch_size=5, filter_model=None):
    """Get a batch of pending or failed experiment runs"""
    try:
        with get_cursor() as cursor:
            query = """
            SELECT model_id, test_case_id, run_number
            FROM experiment_runs
            WHERE (status = 'pending' OR status = 'failed')
            """
            
            params = []
            
            if filter_model:
                query += " AND model_id = %s"
                params.append(filter_model)
                
            query += """
            ORDER BY last_attempt_timestamp ASC NULLS FIRST
            LIMIT %s
            """
            params.append(batch_size)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching pending experiments: {e}")
        return []

def mark_run_as_running(model_id, test_case_id, run_number):
    """Mark an experiment run as 'running'"""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE experiment_runs
                SET status = 'running', last_attempt_timestamp = NOW()
                WHERE model_id = %s AND test_case_id = %s AND run_number = %s;
                """,
                (model_id, test_case_id, run_number)
            )
        return True
    except Exception as e:
        logger.error(f"Error marking run as running: {e}")
        return False

def get_models():
    """Get all available models from the database"""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT name FROM llm_models")
            models = [row[0] for row in cursor.fetchall()]
            return models
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return []

def run_batch_experiments(batch_size=5, wait_time=5, max_retries=3, 
                         filter_model: Optional[str] = None):
    """
    Run a batch of pending experiments
    
    Args:
        batch_size: Number of experiments to process in one batch
        wait_time: Seconds to wait between batches
        max_retries: Maximum number of retry attempts for failed runs
        filter_model: Optional model name to filter experiments
    """
    from app.services.query_with_eval import query_with_eval
    
    total_processed = 0
    
    while True:
        # Get pending runs (with filter if specified)
        pending_runs = get_pending_experiments(batch_size, filter_model)
        
        if not pending_runs:
            logger.info("No more pending experiments found.")
            break
        
        logger.info(f"Running batch of {len(pending_runs)} experiments")
        
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
    
    # Start background thread for remaining runs if needed
    if number_of_runs > 1:
        def run_remaining():
            run_batch_experiments(
                batch_size=number_of_runs-1,  # Exclude the first run
                filter_model=model_id
            )
            
        thread = threading.Thread(target=run_remaining)
        thread.daemon = True
        thread.start()
        
    return results, status_code