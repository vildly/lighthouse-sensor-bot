import logging
from app.conf.postgres import get_cursor

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
    """Update test run counts and status"""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE test_runs
                SET completed_at = CURRENT_TIMESTAMP,
                    successful_tests = %s,
                    failed_api_tests = %s,
                    failed_ragas_tests = %s,
                    status = 'completed'
                WHERE id = %s
                """,
                (successful, api_failed, ragas_failed, test_run_id)
            )
    except Exception as e:
        logger.error(f"Error updating test run: {e}")