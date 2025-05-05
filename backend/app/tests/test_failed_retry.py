import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.services.query_with_eval import query_with_eval
from app.ragas.scripts.test_run_manager import retry_failed_experiment_runs

class TestFailedRetry(unittest.TestCase):
    
    @patch('app.ragas.scripts.test_run_manager.get_failed_runs_for_retry')
    @patch('app.ragas.scripts.test_run_manager.mark_run_as_running')
    @patch('app.services.query_with_eval.run_synthetic_evaluation')
    @patch('app.ragas.scripts.test_run_manager.get_cursor')
    def test_retry_with_failed_status(
        self, 
        mock_get_cursor,
        mock_run_synthetic_evaluation,
        mock_mark_run_as_running,
        mock_get_failed_runs
    ):
        """Test that retry_count is properly updated when a retry fails"""
        
        # Setup test data for a failed run
        model_id = "test-model"
        test_case_id = "1"
        run_number = 1
        current_retry_count = 0
        
        # Mock get_failed_runs_for_retry to return our test case
        mock_get_failed_runs.return_value = [(model_id, test_case_id, run_number, current_retry_count)]
        
        # Create a mock cursor and connection
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_cursor
        mock_get_cursor.return_value = mock_connection
        
        # Mock the fetchone results for status check
        mock_cursor.fetchone.side_effect = [
            # First call: Return status='failed' for the status check
            ('failed', 'API call failed'),
            # Second call: Return retry_count=None for the retry count check
            (None,)
        ]
        
        # Create a DataFrame with a failed API call
        failed_df = pd.DataFrame([{
            'test_no': test_case_id,
            'query': 'Test query',
            'ground_truth': 'Test ground truth',
            'error': 'API call failed',
            'api_call_success': False,
            'ragas_evaluated': False,
            'reference_contexts': []
        }])
        
        # Mock run_synthetic_evaluation to return the failed DataFrame
        mock_run_synthetic_evaluation.return_value = (failed_df, None)
        
        # Run the retry function
        retry_failed_experiment_runs(batch_size=1, max_retries=3, wait_time=0)
        
        # Verify update_experiment_run_status was called with retry_count=1
        # Check the SQL execution for the update
        update_calls = [call for call in mock_cursor.execute.call_args_list 
                       if "UPDATE experiment_runs" in call[0][0] and "retry_count" in call[0][0]]
        
        # Verify at least one update call was made
        self.assertTrue(len(update_calls) > 0, "No update calls with retry_count found")
        
        # Check if the last update call includes retry_count=1
        last_update_call = update_calls[-1]
        self.assertIn("retry_count", last_update_call[0][0])
        
        # Check the parameters - retry_count should be 1
        params = last_update_call[0][1]
        # Find the index of retry_count in the params
        retry_count_index = None
        for i, param in enumerate(params):
            if isinstance(param, int) and param == 1:
                retry_count_index = i
                break
        
        self.assertIsNotNone(retry_count_index, "retry_count=1 not found in update parameters") 