from typing import Dict, Any, List, Tuple
import ast
import logging
import math
from app.ragas.scripts.synthetic_ragas_tests import run_synthetic_evaluation, process_ragas_results
from app.helpers.save_query_to_db import save_query_with_eval_to_db
from flask_socketio import emit
from app.conf.websocket import socketio
import re
from app.conf.postgres import get_cursor
from app.ragas.scripts.test_run_manager import ensure_experiment_runs_populated, update_experiment_run_status


logger = logging.getLogger(__name__)

def query_with_eval(model_id: str, run_number: int = 1) -> Tuple[Dict[str, Any], int]:
    """
    Run evaluation tests for a specific model and save results to the database.
    
    Args:
        model_id: The ID of the LLM model to evaluate
        run_number: The experiment run number (default: 1)
        
    Returns:
        Tuple containing results dictionary and HTTP status code
    """
    try:
        # Emit initial progress update
        try:
            socketio.emit('evaluation_progress', {
                'progress': 0,
                'total': 100,
                'message': f'Starting evaluation run #{run_number}...'
            }, namespace='/query')
        except Exception as e:
            logger.error(f"Error emitting initial progress: {e}")
        
        # Get the evaluation results using the synthetic tests
        # Pass a progress callback function to report progress
        def progress_callback(current, total, message="Evaluating"):
            try:
                percent = int((current / total) * 100)
                socketio.emit('evaluation_progress', {
                    'progress': current,
                    'total': total,
                    'percent': percent,
                    'message': message
                }, namespace='/query')
            except Exception as e:
                logger.error(f"Error emitting progress update: {e}")
      
        
        logger.info(f"Starting synthetic evaluation run #{run_number}...")
        
        # Pass run_number to run_synthetic_evaluation
        df, test_run_id = run_synthetic_evaluation(model_id, progress_callback, run_number)
        logger.info(f"Evaluation complete. DataFrame shape: {df.shape if df is not None else 'None'}")
        logger.info(f"DataFrame columns: {df.columns.tolist() if df is not None else 'None'}")

        # Log the DataFrame contents and size
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"Number of test cases to process: {len(df)}")
        
        # Configure logger to ensure it's displaying
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
        
        # Map RAGAS metric names to our expected names
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
        
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        
        # Calculate average metrics from successful tests
        metrics_to_average = [
            'factual_correctness', 
            'semantic_similarity', 
            'context_recall', 
            'faithfulness', 
            'bleu_score', 
            'non_llm_string_similarity', 
            'rogue_score', 
            'string_present'
        ]
        
        # Initialize results dictionary
        average_metrics = {}
        
        # Process rows with successful RAGAS evaluations
        successful_rows = df[df['ragas_evaluated'] == True]
        
        if len(successful_rows) > 0:
            # Extract and process RAGAS results from each successful row
            all_metrics = []
            
            for _, row in successful_rows.iterrows():
                row_ragas_results = row.get('ragas_results')
                if row_ragas_results:
                    # Process the RAGAS results
                    processed_results = process_ragas_results(row_ragas_results, {
                        "reference_contexts": row.get('reference_contexts', []),
                        "ground_truth": row.get('ground_truth', "")
                    })
                    all_metrics.append(processed_results)
            
            # Calculate averages for each metric
            for metric in metrics_to_average:
                values = [m.get(metric) for m in all_metrics if m.get(metric) is not None]
                if values:
                    average_metrics[metric] = sum(values) / len(values)
        
        # For each test case in df, save the query and evaluation results to the database
        total_rows = len(df)
        for i, row in df.iterrows():
            try:
                # Calculate progress percentage for this row
                row_progress = int(50 + ((i + 1) / total_rows) * 40)  # Scale to 50-90% range
                
                # Update progress for each row
                try:
                    socketio.emit('evaluation_progress', {
                        'progress': row_progress,
                        'total': 100,
                        'percent': row_progress,
                        'message': f'Processing test case {i+1} of {total_rows}...'
                    }, namespace='/query')
                except Exception as e:
                    logger.error(f"Error emitting row progress: {e}")
                
                # Handle different possible column names for the question
                query = row.get('query')
                if query is None:
                    logger.error(f"No question/query column found in row. Available columns: {row.index.tolist()}")
                    continue
                    
                response = row.get('response')
                if response is None:
                    logger.error(f"No response column found in row. Available columns: {row.index.tolist()}")
                    continue
                
                # Extract SQL queries from context
                sql_queries = []
                if row.get('context'):
                    for item in row.get('context', []):
                        if isinstance(item, str) and item.startswith("SQL Query: "):
                            sql_query = item.replace("SQL Query: ", "", 1)
                            sql_queries.append(sql_query)
                
                # Get token_usage directly from the row
                token_usage = row.get('token_usage')

                # Create evaluation results dictionary 
                evaluation_data = {
                    # Convert reference_contexts to a string if it's a list
                    "retrieved_contexts": str(row.get('reference_contexts', [])) if isinstance(row.get('reference_contexts'), list) else str(row.get('reference_contexts', [])),
                    "ground_truth": row.get('ground_truth'),
                }
                
                # Get test_no for experiment tracking
                test_id = str(row.get('test_no', ''))
                
                # Update experiment run status based on the results
                status = 'success' if row.get('ragas_evaluated', False) else 'failed'
                error_msg = row.get('ragas_error') if status == 'failed' else None
                
                # Update experiment tracking tables
                update_experiment_run_status(model_id, test_id, run_number, status, error_msg)
                
                row_ragas_results = row.get('ragas_results')
                if row_ragas_results:
                    # Process the RAGAS results for this specific row
                    row_results_dict = {}
                    
                    # Handle different types of RAGAS results
                    if hasattr(row_ragas_results, 'to_pandas'):
                        # Convert to pandas DataFrame and then to dict
                        df_result = row_ragas_results.to_pandas()
                        if not df_result.empty:
                            row_results_dict = df_result.iloc[0].to_dict()
                    elif isinstance(row_ragas_results, dict):
                        row_results_dict = row_ragas_results
                    else:
                        # Try to convert string representation to dict
                        results_str = str(row_ragas_results)
                        if '{' in results_str and '}' in results_str:
                            dict_part = results_str[results_str.find('{'): results_str.rfind('}')+1]
                            try:
                                row_results_dict = ast.literal_eval(dict_part)
                            except:
                                row_results_dict = {}
                    
                    # Map the metrics using our mapping dictionary
                    for ragas_key, our_key in metric_mapping.items():
                        value = row_results_dict.get(ragas_key)
                        # Check if value is NaN and replace with None
                        if isinstance(value, float) and math.isnan(value):
                            evaluation_data[our_key] = None
                        else:
                            evaluation_data[our_key] = value
                
                # Save the query with evaluation results
                query_result_id = save_query_with_eval_to_db(
                    query=query,
                    direct_response=response,
                    full_response=row.get('context', ''),
                    llm_model_id=model_id,
                    evaluation_results=evaluation_data,
                    sql_queries=sql_queries,
                    token_usage=token_usage
                )

            except Exception as e:
                logger.error(f"Error saving evaluation for query {i+1}/{total_rows}: {e}")
                
                # Update experiment run status to failed if there was an error saving
                test_id = str(row.get('test_no', ''))
                update_experiment_run_status(model_id, test_id, run_number, 'failed', str(e))
        
        # Emit progress update for database saving
        try:
            socketio.emit('evaluation_progress', {
                'progress': 90,
                'total': 100,
                'percent': 90,
                'message': 'Saving results to database...'
            }, namespace='/query')
        except Exception as e:
            logger.error(f"Error emitting database progress: {e}")
            
        # Format the full response data from the dataframe
        full_response_data = []
        for _, row in df.iterrows():
            full_response_data.append({
                "query": row.get('query', ''),
                "ground_truth": row.get('ground_truth', ''),
                "response": row.get('response', ''),
                "context": row.get('context', '')
            })
        
        # Format the full response as markdown
        full_response_md = "# Evaluation Results\n\n"
        for i, item in enumerate(full_response_data):
            full_response_md += f"## Test Case {i+1}\n\n"
            full_response_md += f"### Question\n{item['query']}\n\n"
            full_response_md += f"### Ground Truth\n{item['ground_truth']}\n\n"
            full_response_md += f"### Model Response\n{item['response']}\n\n"
            if item['context']:
                full_response_md += f"### Full response\n{item['context']}\n\n"
            full_response_md += "---\n\n"
        
        # Emit completion progress update
        try:
            socketio.emit('evaluation_progress', {
                'progress': 100,
                'total': 100,
                'percent': 100,
                'message': 'Evaluation complete!'
            }, namespace='/query')
        except Exception as e:
            logger.error(f"Error emitting completion progress: {e}")
        
        # Return both the results and the full response
        return {
            "results": average_metrics,
            "full_response": full_response_md
        }, 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Synthetic evaluation failed: {str(e)}")
        
        # Emit error progress update
        try:
            socketio.emit('evaluation_progress', {
                'progress': -1,
                'total': 100,
                'percent': 0,
                'message': f'Error: {str(e)}'
            }, namespace='/query')
        except Exception as emit_error:
            logger.error(f"Error emitting error progress: {emit_error}")
            
        return {
            "error": f"Synthetic evaluation failed: {str(e)}",
            "results": {"error": str(e)},
            "full_response": f"Error during evaluation: {str(e)}"
        }, 500 