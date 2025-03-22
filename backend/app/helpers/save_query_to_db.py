from agno.utils.log import logger
from app.conf.postgres import get_cursor
import re


def get_model_id(llm_model_name):
    """
    Get the model ID from the database
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT id FROM llm_model WHERE name = %s", (llm_model_name,))

        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"No model found with name: {llm_model_name}")

    model_id = result[0]

    return model_id


def save_query_to_db(
    query, direct_response, full_Response, llm_model_id, sql_queries=None
):
    """Save the query and response to the database

    Args:
        query: The original question asked
        direct: The direct response from the agent
        full_response: The full response from the agent including reasoning and SQL queries
        sql_queries: List of SQL queries executed (optional)
    Returns:
        query_id: The ID of the saved query
    """
    with get_cursor() as cursor:
        cursor.execute(
            """INSERT INTO query_result (query, direct_response, full_response, sql_queries, 
          llm_model_id) VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (
                query,
                direct_response,
                full_Response,
                sql_queries,
                get_model_id(llm_model_id),
            ),
        )
    query_id = cursor.fetchone()[0]

    if not query_id:
        raise ValueError("Query ID not found")

    return query_id


def save_query_with_eval_to_db(
    query, direct_response, full_response, evaluation_results, sql_queries=None
):
    """Save the query and response to the database with evaluation results

    Args:
        query: The original question asked
        direct_response: The direct response from the agent
        full_response: The full response from the agent including reasoning and SQL queries
        evaluation_results: The evaluation results for the query as a JSON object (dict)
        sql_queries: List of SQL queries executed (optional)
    """
    if not isinstance(evaluation_results, dict):
        raise ValueError("Evaluation results must be a dictionary")

    required_keys = {
        "retrieved_contexts": (str, type(None)),
        "reference": (str, type(None)),
        "factual_correctness": (float, int, type(None)),
        "semantic_similarity": (float, int, type(None)),
        "context_recall": (float, int, type(None)),
        "faithfulness": (float, int, type(None)),
        "bleu_score": (float, int, type(None)),
        "non_llm_string_similarity": (float, int, type(None)),
        "rogue_score": (float, int, type(None)),
        "string_present": (bool, type(None)),
    }

    for key, expected_types in required_keys.items():
        value = evaluation_results.get(key)
        if value is not None and not isinstance(value, expected_types):
            raise ValueError(
                f"Invalid type for {key}: expected {expected_types}, got {type(value)}"
            )

    query_result_id = save_query_to_db(
        query, direct_response, full_response, sql_queries
    )

    with get_cursor() as cursor:

        cursor.execute(
            """INSERT INTO query_evaluation (retrieved_contexts, reference, factual_correctness, semantic_similarity, 
          context_recall, faithfulness, bleu_score, non_llm_string_similarity, rogue_score, string_present, 
          query_result_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                evaluation_results.get("retrieved_contexts"),
                evaluation_results.get("reference"),
                evaluation_results.get("factual_correctness"),
                evaluation_results.get("semantic_similarity"),
                evaluation_results.get("context_recall"),
                evaluation_results.get("faithfulness"),
                evaluation_results.get("bleu_score"),
                evaluation_results.get("non_llm_string_similarity"),
                evaluation_results.get("rogue_score"),
                evaluation_results.get("string_present"),
                query_result_id,
            ),
        )
