from typing import Dict, Any, List, Tuple, Optional
import ast
import logging
import math
import os
import json
import re
import io
from app.ragas.scripts.synthetic_ragas_tests import run_synthetic_evaluation
from app.helpers.save_query_to_db import save_query_to_db, save_query_with_eval_to_db
from flask_socketio import emit
from app.conf.websocket import socketio
from app.ragas.scripts.test_run_manager import execute_test_runs
from app.helpers.extract_answer import extract_answer_for_evaluation
from app.helpers.extract_token_usage import extract_token_usage
from app.utils.websocket_logger import WebSocketLogHandler
from app.helpers.get_analyst import get_data_analyst
from agno.utils.log import logger as agno_logger


logger = logging.getLogger(__name__)

def query_with_eval(model_id: str, number_of_runs: int = 1, max_retries: int = 3, existing_query_result_id: Optional[int] = None) -> Tuple[Dict[str, Any], int]:
    """
    Run evaluation tests for a specific model with retry logic.
    
    Args:
        model_id: The ID of the LLM model to evaluate
        number_of_runs: Number of times each test should run successfully
        max_retries: Maximum number of retry attempts for failed tests
        existing_query_result_id: Existing query result ID to pass to execute_test_runs
        
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
        
        # Define progress callback
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
        
        # Use the execute_test_runs function with custom max_retries
        logger.info(f"Starting synthetic evaluation with retry logic (max_retries={max_retries})...")
        ragas_results, df = execute_test_runs(
            model_id, 
            number_of_runs=number_of_runs, 
            max_retries=max_retries,
            progress_callback=progress_callback
        )
        
        logger.info(f"Evaluation complete. DataFrame shape: {df.shape if df is not None else 'None'}")
        logger.info(f"DataFrame columns: {df.columns.tolist() if df is not None else 'None'}")

        # Log the DataFrame contents and size
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"Number of test cases to process: {len(df)}")
        
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
        
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        
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
                
                # Map the metrics using our mapping dictionary
                for ragas_key, our_key in metric_mapping.items():
                    value = results_dict.get(ragas_key)
                    # Check if value is NaN and replace with None
                    if isinstance(value, float) and math.isnan(value):
                        evaluation_data[our_key] = None
                    else:
                        evaluation_data[our_key] = value
                
                # Save the query with evaluation results directly using save_query_with_eval_to_db
                # No need to manage existing_query_result_id as the function handles this internally
                save_query_with_eval_to_db(
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
        
        # Emit progress for database saving
        try:
            socketio.emit('evaluation_progress', {
                'progress': 90,
                'total': 100,
                'percent': 90,
                'message': 'Processing evaluation results...'
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
        
def process_query_internal(question: str, source_file: Optional[str] = None, llm_model_id: Optional[str] = None, save_to_db: bool = True) -> Dict[str, Any]:
    """Process a query internally without going through the API
    
    Args:
        question: The user's question
        source_file: Optional source file to use
        llm_model_id: Optional model ID
        save_to_db: Whether to save the query to database
        
    Returns:
        Dict with query results
    """
    try:
        # Set up to capture SQL queries
        sql_queries = []

        # Set up to capture logger output
        log_capture = io.StringIO()
        log_handler = logging.StreamHandler(log_capture)
        log_handler.setLevel(logging.INFO)
        
        # Use the same logger that works in query.py
        agno_logger.addHandler(log_handler)
        
        # Add WebSocket log handler
        websocket_handler = WebSocketLogHandler()
        websocket_handler.setLevel(logging.INFO)
        agno_logger.addHandler(websocket_handler)
        
        # Get the data analyst agent
        data_analyst = get_data_analyst(source_file, llm_model_id)
        
        # If source_file is provided, add it to the question
        if source_file:
            question = f"{question} (Use data from {source_file})"
        
        # Run the agent
        response = data_analyst.run(question)
        
        # Extract token usage
        token_usage = extract_token_usage(response)
        
        # Remove the log handlers
        agno_logger.removeHandler(log_handler)
        agno_logger.removeHandler(websocket_handler)
        
        # Extract SQL queries from log output
        log_output = log_capture.getvalue()
        print(f"DEBUG - Log output length: {len(log_output)} bytes")
        
        current_query = ""
        for line in log_output.splitlines():
            if "Running:" in line:
                # If we have a query in progress, save it before starting a new one
                if current_query:
                    sql_queries.append(current_query.strip())
                    current_query = ""

                # Start a new query
                current_query = line.split("Running:", 1)[1].strip()
            elif current_query and line.strip() and not line.strip().startswith("INFO"):
                # Continue the current query with this line
                current_query += " " + line.strip()

        # Add the last query if there is one
        if current_query:
            sql_queries.append(current_query.strip())

        # Print the extracted queries for debugging
        print(f"Extracted SQL queries: {sql_queries}")

        # Remove duplicates while preserving order
        unique_queries = []
        for query in sql_queries:
            if query not in unique_queries:
                unique_queries.append(query)
        sql_queries = unique_queries

        # Format the full response as markdown
        fullResponse = "# Query Results\n\n"
        fullResponse += f"## Question\n{question}\n\n"
        if sql_queries:
            fullResponse += "## SQL Queries\n"
            for sql in sql_queries:
                fullResponse += f"```sql\n{sql}\n```\n\n"
        fullResponse += f"## Response\n{response.content}\n\n"
        
        # Extract clean answer
        clean_answer = extract_answer_for_evaluation(response.content)
        
        # Save the query and response to the database if requested
        query_result_id = None
        if save_to_db and llm_model_id:
            try:
                query_result_id = save_query_to_db(
                    query=question,
                    direct_response=clean_answer,
                    full_response=fullResponse,
                    llm_model_id=llm_model_id,
                    sql_queries=sql_queries,
                    token_usage=token_usage,
                )
                logger.info(f"Query saved to database with model ID: {llm_model_id}, query_result_id: {query_result_id}")
            except Exception as db_error:
                logger.error(f"Failed to save query to database: {str(db_error)}")
                # Don't raise here, just log the error and continue

        # Return the results
        return {
            "content": clean_answer,
            "full_response": fullResponse,
            "sql_queries": sql_queries,
            "token_usage": token_usage,
            "query_result_id": query_result_id
        }
        
    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        logger.error(error_message)
        return {"error": error_message, "content": f"Error: {str(e)}"}
