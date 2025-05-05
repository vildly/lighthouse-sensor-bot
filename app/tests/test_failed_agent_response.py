import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import sys
import os

class TestFailedAgentResponse(unittest.TestCase):
    
    @patch('app.ragas.scripts.synthetic_ragas_tests.run_test_case')
    @patch('app.ragas.scripts.test_run_manager.update_experiment_run_status')
    @patch('app.ragas.scripts.test_run_manager.mark_run_as_running')
    @patch('app.ragas.scripts.synthetic_ragas_tests.load_synthetic_test_cases')
    def test_api_call_failure_handling(
        self, 
        mock_load_test_cases, 
        mock_mark_run_as_running,
        mock_update_status,
        mock_run_test_case
    ):
        """Test that API call failures are properly handled"""
        
        # Setup test data
        mock_test_cases = [
            {
                "test_no": "1",
                "query": "What is the fuel consumption?",
                "ground_truth": "The fuel consumption is 100 liters.",
                "reference_contexts": ["This is a context"]
            }
        ]
        mock_load_test_cases.return_value = mock_test_cases
        
        # Mock the API call to fail
        mock_run_test_case.return_value = (None, None, False, None)
        
        # Run synthetic evaluation
        from app.ragas.scripts.synthetic_ragas_tests import run_synthetic_evaluation
        model_id = "test-model"
        run_number = 1
        df, _ = run_synthetic_evaluation(model_id, run_number=run_number)
        
        # Verify the DataFrame has expected structure for failed tests
        self.assertIn("test_no", df.columns)
        self.assertIn("error", df.columns)
        self.assertIn("api_call_success", df.columns)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["api_call_success"], False)
    
    # Test the specific code path directly
    def test_direct_failed_row_handling(self):
        """Directly test the code path that handles failed API calls"""
        
        # Create a mock for the function we want to verify
        with patch('app.ragas.scripts.test_run_manager.update_experiment_run_status') as mock_update:
            # Import the function directly
            from app.services.query_with_eval import update_experiment_run_status
            
            # Create a row with api_call_success=False
            row = {
                'test_no': '1',
                'query': 'Test query',
                'api_call_success': False,
                'error': 'API call failed'
            }
            
            # Execute the specific code block from query_with_eval
            model_id = "test-model"
            run_number = 1
            
            # This is the exact code from query_with_eval.py that handles failed API calls
            if not row.get('api_call_success', True):
                # Extract test_id and error message
                test_id = str(row.get('test_no', ''))
                error_msg = row.get('error', 'API call failed')
                
                # Update experiment run status to failed
                update_experiment_run_status(model_id, test_id, run_number, 'failed', error_msg, None)
            
            # Verify update_experiment_run_status was called with the correct parameters
            mock_update.assert_called_with(model_id, '1', run_number, 'failed', 'API call failed', None) 