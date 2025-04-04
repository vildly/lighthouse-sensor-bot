from typing import Dict, Any, List, Tuple
import ast
import logging
from app.ragas.scripts.synthetic_ragas_tests import run_synthetic_evaluation
from app.helpers.save_query_to_db import save_query_with_eval_to_db
from flask_socketio import emit
from app.conf.websocket import socketio
import re

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
            
        # Format the full response data from the dataframe
        full_response_data = []
        for _, row in df.iterrows():
            full_response_data.append({
                "question": row.get('user_input', ''),
                "reference": row.get('reference', ''),
                "response": row.get('response', ''),
                "context": row.get('context', '')
            })
        
        # Format the full response as markdown
        full_response_md = "# Evaluation Results\n\n"
        for i, item in enumerate(full_response_data):
            full_response_md += f"## Test Case {i+1}\n\n"
            full_response_md += f"### Question\n{item['question']}\n\n"
            full_response_md += f"### Reference Answer\n{item['reference']}\n\n"
            full_response_md += f"### Model Response\n{item['response']}\n\n"
            if item['context']:
                full_response_md += f"### Context\n{item['context']}\n\n"
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
            "results": results_dict,
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

def extract_answer_for_evaluation(response):
    """Extract the answer from the model's response for evaluation purposes."""
    
    # Extract the answer section using regex - get the LAST answer section
    answer_sections = re.findall(
        r"## Answer\s*(.*?)(?=\s*##|$)", response, re.DOTALL
    )
    if answer_sections:
        clean_answer = answer_sections[-1].strip()  # Use the last answer section
    else:
        # Check if there's an "Agent Reasoning and Response:" prefix
        if "Agent Reasoning and Response:" in response:
            response = response.split("Agent Reasoning and Response:")[1].strip()
        
        # Try to find any section that looks like an answer
        answer_match = re.search(r"(?:###|##)\s*(?:Answer|Key Details.*?)\s*(.*?)(?=\s*(?:###|##)|$)", response, re.DOTALL)
        if answer_match:
            clean_answer = answer_match.group(1).strip()
        else:
            # Fallback: Split on the Analysis section header to get just the answer
            parts = response.split("## Analysis")
            clean_answer = parts[-1].strip() if len(parts) > 1 else response.strip()
    
    # Remove any remaining markdown headers
    clean_answer = re.sub(r"^###\s*.*?\n", "", clean_answer, flags=re.MULTILINE)
    
    # If we still don't have a clean answer, use the original response
    if not clean_answer or clean_answer.isspace():
        clean_answer = response
    
    return clean_answer 