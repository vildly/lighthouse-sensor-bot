import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.services.query_with_eval import query_with_eval


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
        
        # Run synthetic evaluation - Import here to use the patched version if needed
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
        
        # Run query_with_eval with the DataFrame
        # Patch run_synthetic_evaluation where it's imported by query_with_eval
        with patch('app.services.query_with_eval.run_synthetic_evaluation', return_value=(df, None)), \
             patch('app.services.query_with_eval.update_experiment_run_status') as mock_update_exp_status:
            query_with_eval(model_id, run_number)
            
            # Verify update_experiment_run_status was called with the right parameters
            mock_update_exp_status.assert_called()
            
            # Get the arguments from the call
            call_args = mock_update_exp_status.call_args[0]
            
            # Verify model_id and run_number match
            self.assertEqual(call_args[0], model_id)
            self.assertEqual(call_args[2], run_number)
            
            # Verify status is 'failed'
            self.assertEqual(call_args[3], 'failed')
            
            # Verify query_evaluation_id is None
            self.assertIsNone(call_args[5])
    
    @patch('app.helpers.save_query_to_db.save_query_with_eval_to_db')
    # Patch update_experiment_run_status where it's imported by query_with_eval
    @patch('app.services.query_with_eval.update_experiment_run_status') 
    def test_failed_row_handling_in_query_with_eval(self, mock_update_status, mock_save_query):
        """Test that query_with_eval properly handles rows with failed API calls"""
        
        # Create a test DataFrame with a failed row
        df = pd.DataFrame([{
            'test_no': '1',
            'query': 'Test query',
            'ground_truth': 'Test ground truth',
            'error': 'API call failed',
            'api_call_success': False,
            'ragas_evaluated': False,
            'reference_contexts': []
        }])
        
        # Mock run_synthetic_evaluation where it's imported by query_with_eval
        with patch('app.services.query_with_eval.run_synthetic_evaluation', 
                  return_value=(df, None)):
            
            # Run query_with_eval
            model_id = "test-model"
            run_number = 1
            query_with_eval(model_id, run_number)
            
            # Verify update_experiment_run_status was called correctly
            mock_update_status.assert_called_with(
                model_id, '1', run_number, 'failed', 'API call failed', None
            )
            
            # Verify save_query_with_eval_to_db was NOT called (should be skipped for failed rows)
            mock_save_query.assert_not_called()


if __name__ == '__main__':
    unittest.main() 