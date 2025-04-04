from typing import Dict, Any, List, Tuple
import ast
import logging
from app.ragas.scripts.synthetic_ragas_tests import run_synthetic_evaluation
from app.helpers.save_query_to_db import save_query_with_eval_to_db
from flask_socketio import emit
from app.conf.websocket import socketio

logger = logging.getLogger(__name__)

def query_with_eval(model_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Run evaluation tests for a specific model and save results to the database.
    
    Args:
        model_id: The ID of the LLM model to evaluate
        
    Returns:
        Tuple containing results dictionary and HTTP status code
    """
    try:
        # Emit initial progress update
        try:
            socketio.emit('evaluation_progress', {
                'progress': 0,
                'total': 100,
                'message': 'Starting evaluation...'
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
        
        ragas_results, df = run_synthetic_evaluation(model_id, progress_callback)

        # Configure logger to ensure it's displaying
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
        
        # Process RAGAS results into a consistent dictionary format
        results_dict = {}
        if isinstance(ragas_results, dict):
            results_dict = ragas_results

        else:
            # Try to convert to string and parse
            results_str = str(ragas_results)

            if '{' in results_str and '}' in results_str:
                dict_part = results_str[results_str.find('{'): results_str.rfind('}')+1]
                try:
                    parsed_dict = ast.literal_eval(dict_part)
                    for k, v in parsed_dict.items():
                        if isinstance(v, (int, float)):
                            results_dict[k] = float(v)
                        else:
                            results_dict[k] = v
                except (SyntaxError, ValueError):
                    results_dict["raw_results"] = results_str
        
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
        
        # For each test case in df, save the query and evaluation results to the database
        for i, row in df.iterrows():
            try:
                query = row['user_input']
                response = row['response']
                
                # Extract SQL queries from context
                sql_queries = []
                if row.get('context'):
                    for item in row.get('context', []):
                        if isinstance(item, str) and item.startswith("SQL Query: "):
                            sql_query = item.replace("SQL Query: ", "", 1)
                            sql_queries.append(sql_query)
                
                # Create evaluation results dictionary with the metrics from ragas_results
                evaluation_data = {
                    "retrieved_contexts": str(row.get('retrieved_contexts', [])),
                    "reference": row.get('reference'),
                }
                
                # Map the metrics using our mapping dictionary
                for ragas_key, our_key in metric_mapping.items():
                    evaluation_data[our_key] = results_dict.get(ragas_key)
                
                # Save the query with evaluation results
                save_query_with_eval_to_db(
                    query=query,
                    direct_response=response,
                    full_response=row.get('context', ''),
                    llm_model_id=model_id,
                    evaluation_results=evaluation_data,
                    sql_queries=sql_queries
                )
            except Exception as e:
                logger.error(f"Error saving evaluation for query {query}: {e}")
        
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
        
        return {"results": results_dict}, 200
        
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
            "results": {"error": str(e)}
        }, 500 