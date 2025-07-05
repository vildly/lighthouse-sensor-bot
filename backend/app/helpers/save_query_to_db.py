from typing import Dict, Optional, List, Union, Tuple, Any
from agno.utils.log import logger
from app.conf.postgres import get_cursor
import ast
import json
import logging


def get_model_id(llm_model_name: str) -> int:
    with get_cursor() as cursor:
        cursor.execute("SELECT id FROM llm_models WHERE name = %s", (llm_model_name,))
        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"No model found with name: {llm_model_name}")
        return result[0]


def save_query_to_db(
    query: str,
    direct_response: str,
    full_response: str,
    llm_model_id: str,
    sql_queries: Optional[List[str]] = None,
    token_usage: Optional[Dict[str, int]] = None,
    test_no: Optional[int] = None,
) -> int:
    """Save the query and response to the database.
    
    Returns:
        int: The ID of the inserted query_result record
    """
    # Convert Python structures to JSON strings for PostgreSQL
    
    # Get numeric model ID from name
    model_id = get_model_id(llm_model_id)
    
    with get_cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO query_result (query, direct_response, full_response, llm_model_id, sql_queries, test_no)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (query, direct_response, full_response, model_id, sql_queries, test_no),
            )
            
            # Get the ID of the inserted record
            query_result_id = cursor.fetchone()[0]
            
            # If token usage is provided, insert into token_usage table
            if token_usage:
                prompt_tokens = token_usage.get("prompt_tokens")
                completion_tokens = token_usage.get("completion_tokens")
                total_tokens = token_usage.get("total_tokens")
                
                cursor.execute(
                    """
                    INSERT INTO token_usage (prompt_tokens, completion_tokens, total_tokens, query_result_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (prompt_tokens, completion_tokens, total_tokens, query_result_id),
                )
            
            return query_result_id
            
        except Exception as e:
            logger.error(f"Error saving query to database: {e}")
            raise


def create_query_result_for_eval(
    query: str,
    direct_response: str,
    full_response: str,
    llm_model_id: str,
    sql_queries: Optional[List[str]] = None,
    test_no: Optional[int] = None,
    tool_calls: Optional[str] = None,
) -> int:
    """Create a query_result record for evaluation purposes.
    
    Returns:
        int: The ID of the inserted query_result record
    """
    # Convert Python structures to JSON strings for PostgreSQL
    sql_queries_json = json.dumps(sql_queries) if sql_queries else None
    
    # Get numeric model ID from name
    model_id = get_model_id(llm_model_id)
    
    with get_cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO query_result (query, direct_response, full_response, llm_model_id, sql_queries, test_no, tool_calls)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (query, direct_response, full_response, model_id, sql_queries_json, test_no, tool_calls),
            )
            
            # Get the ID of the inserted record
            query_result_id = cursor.fetchone()[0]
            return query_result_id
            
        except Exception as e:
            logger.error(f"Error creating query_result record: {e}")
            raise


def save_query_with_eval_to_db(
    query: str,
    direct_response: str,
    full_response: str,
    llm_model_id: str,
    evaluation_results: Dict[str, Union[str, float, int, bool, None]],
    sql_queries: Optional[List[str]] = None,
    token_usage: Optional[Dict[str, int]] = None,
    existing_query_result_id: Optional[int] = None,
    test_no: Optional[int] = None,
    tool_calls: Optional[str] = None,
) -> int:
    """Save the query evaluation results to the database.
    
    Returns:
        int: The ID of the inserted query_evaluation record
    """
    if not isinstance(evaluation_results, dict):
      raise ValueError("Evaluation results must be a dictionary")

    # Log the incoming evaluation results for debugging
    print(f"DEBUG - Evaluation results before saving: {evaluation_results}")

    required_keys = {
        "retrieved_contexts": (str, type(None)),
        "ground_truth": (str, type(None)),
        "factual_correctness": (float, int, type(None)),
        "semantic_similarity": (float, int, type(None)),
        "context_recall": (float, int, type(None)),
        "faithfulness": (float, int, type(None)),
        "bleu_score": (float, int, type(None)),
        "non_llm_string_similarity": (float, int, type(None)),
        "rogue_score": (float, int, type(None)),
        "string_present": (float, int, type(None)),
    }

    # Make a copy of evaluation_results to avoid modifying the original
    processed_results = evaluation_results.copy()

    # Fix any type issues and ensure all required keys exist
    for key, expected_types in required_keys.items():
        value = processed_results.get(key)
        
        # Convert to proper numeric type if needed
        if value is not None:
            if not isinstance(value, expected_types):
                try:
                    if float in expected_types or int in expected_types:
                        processed_results[key] = float(value)
                    elif str in expected_types:
                        processed_results[key] = str(value)
                except (ValueError, TypeError):
                    print(f"DEBUG - Could not convert {key}={value} to expected type {expected_types}")
                    processed_results[key] = None
        else:
            # Ensure the key exists even if the value is None
            processed_results[key] = None

    # Log the processed evaluation results for debugging
    print(f"DEBUG - Processed evaluation results for DB: {processed_results}")

    # Use existing query_result_id if provided, otherwise create a new record
    query_result_id = existing_query_result_id
    if query_result_id is None:
        query_result_id = create_query_result_for_eval(
            query, direct_response, full_response, llm_model_id, sql_queries, test_no, tool_calls
        )

    with get_cursor() as cursor:
        try:
            # Insert evaluation metrics record
            insert_values = (
                processed_results.get("factual_correctness"),
                processed_results.get("semantic_similarity"),
                processed_results.get("context_recall"),
                processed_results.get("faithfulness"),
                processed_results.get("bleu_score"),
                processed_results.get("non_llm_string_similarity"),
                processed_results.get("rogue_score"),
                processed_results.get("string_present"),
            )
            
            # Print actual values being inserted for debugging
            print(f"DEBUG - DB insert values: {insert_values}")
            
            cursor.execute(
                """
                INSERT INTO evaluation_metrics (
                    factual_correctness, semantic_similarity, context_recall, 
                    faithfulness, bleu_score, non_llm_string_similarity,
                    rogue_score, string_present
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                insert_values
            )
            evaluation_metrics_id = cursor.fetchone()[0]
            
            # Then insert into query_evaluation
            cursor.execute(
                """
                INSERT INTO query_evaluation (
                    retrieved_contexts, ground_truth, query_result_id, evaluation_metrics_id
                ) VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (
                    processed_results.get("retrieved_contexts"),
                    processed_results.get("ground_truth"),
                    query_result_id,
                    evaluation_metrics_id,
                ),
            )
            query_evaluation_id = cursor.fetchone()[0]
            
            # If token usage is provided, insert into the separate token_usage table
            if token_usage:
                prompt_tokens = token_usage.get("prompt_tokens")
                completion_tokens = token_usage.get("completion_tokens")
                total_tokens = token_usage.get("total_tokens")
                
                cursor.execute(
                    """
                    INSERT INTO token_usage (prompt_tokens, completion_tokens, total_tokens, query_result_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (prompt_tokens, completion_tokens, total_tokens, query_result_id),
                )
                
            return query_evaluation_id
        except Exception as e:
            logger.error(f"Error saving evaluation results to database: {e}")
            raise