from typing import Dict, Any, List, Tuple, Optional
import ast
import logging
import math
import os
import json
import re
import io
import pandas as pd
from app.helpers.save_query_to_db import save_query_to_db
from app.helpers.extract_answer import extract_answer_for_evaluation
from app.helpers.extract_token_usage import extract_token_usage
from app.utils.websocket_logger import WebSocketLogHandler
from app.helpers.get_analyst import get_data_analyst
from agno.utils.log import logger as agno_logger
from flask_socketio import emit
from app.conf.websocket import socketio


logger = logging.getLogger(__name__)

def query_with_eval(model_id, number_of_runs=1, max_retries=3, progress_callback=None, test_selection=None):
    """
    Process queries and evaluate them.
    This function is the entry point for running evaluation tests.
    Tests are loaded from the test_cases json file directly by test_run_manager.
    
    Args:
        model_id: ID of the model to use
        number_of_runs: Number of runs per test
        max_retries: Maximum number of retries per test
        progress_callback: Optional callback for progress updates
        test_selection: Optional string specifying which tests to run (e.g., "1", "1,3,5", "1-3")
    
    Returns:
        For API usage: (response_dict, status_code)
        For direct usage: (combined_ragas_results, results_df)
    """
    logger.info(f"Starting evaluation for model: {model_id}")
    
    try:
        # Import here to avoid circular dependencies
        from app.ragas.scripts.test_run_manager import execute_test_runs
        
        # Run the tests - test_data parameter is None so test_run_manager will load cases from JSON
        combined_ragas_results, results_df = execute_test_runs(
            model_id=model_id, 
            number_of_runs=number_of_runs,
            max_retries=max_retries,
            progress_callback=progress_callback,
            test_data=None,  # Let test_run_manager load test cases from JSON
            test_selection=test_selection  # Pass test selection to execute_test_runs
        )
        
        # Check if this is being called from the API (look at the call stack)
        import inspect
        frame = inspect.currentframe()
        calling_function = None
        try:
            if frame and frame.f_back and frame.f_back.f_code:
                calling_function = frame.f_back.f_code.co_name
        finally:
            del frame
            
        # If called from API endpoint, return API format
        if calling_function == "evaluate_endpoint":
            # Format response for API
            response_dict = {
                "status": "success",
                "message": "Evaluation completed successfully",
                "results": combined_ragas_results,
                "summary": {
                    "total_tests": len(results_df) if results_df is not None else 0,
                    "model_id": model_id,
                    "number_of_runs": number_of_runs,
                    "max_retries": max_retries
                }
            }
            
            # Add metrics if available
            if results_df is not None and not results_df.empty:
                numeric_cols = results_df.select_dtypes(include=['float64', 'int64']).columns
                metrics = {}
                for col in numeric_cols:
                    if col.startswith(('factual_', 'semantic_', 'context_', 'faithfulness')):
                        metrics[col] = float(results_df[col].mean()) if results_df[col].notna().any() else None
                
                if metrics:
                    response_dict["metrics"] = metrics
            
            return response_dict, 200
        else:
            # Return original format for direct usage
            return combined_ragas_results, results_df
            
    except Exception as e:
        logger.error(f"Error in query_with_eval: {e}")
        
        # Check if this is being called from the API
        import inspect
        frame = inspect.currentframe()
        calling_function = None
        try:
            if frame and frame.f_back and frame.f_back.f_code:
                calling_function = frame.f_back.f_code.co_name
        finally:
            del frame
            
        # If called from API endpoint, return API error format
        if calling_function == "evaluate_endpoint":
            return {
                "status": "error",
                "message": f"Evaluation failed: {str(e)}",
                "error": str(e)
            }, 500
        else:
            # Re-raise for direct usage
            raise

# Remove the save_query_with_eval_to_db function completely
# All DB operations should go through app.helpers.save_query_to_db directly

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
    print("DEBUG: Entered process_query_internal")
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
        
        # Extract tool calls as a list of tool names
        print(f"DEBUG: response type: {type(response)}")
        print(f"DEBUG: response: {response}")
        tool_calls_list = None
        print(f"DEBUG: Has a tools attribute: {hasattr(response, 'tools')}")
        print(f"DEBUG: Tools: {response.tools}")
        
        # Extract tool names from the tools attribute
        if hasattr(response, "tools") and response.tools:
            print(f"DEBUG: response.tools: {response.tools}")
            tool_calls_list = []
            for tool_call in response.tools:
                print(f"DEBUG: Processing tool call: {tool_call}")
                if isinstance(tool_call, dict) and "tool_name" in tool_call:
                    tool_calls_list.append(tool_call["tool_name"])
                elif hasattr(tool_call, "tool_name"):
                    tool_calls_list.append(tool_call.tool_name)
                else:
                    print(f"DEBUG: Could not extract tool name from: {tool_call}")
        
        print(f"DEBUG: Final tool_calls_list: {tool_calls_list}")
        
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
        
        print(f"DEBUG - FULL RESPONSE: {fullResponse}")
        
        # Extract clean answer
        clean_answer = extract_answer_for_evaluation(response.content)
        
        # Save the query and response to the database if requested
        query_result_id = None
        # if save_to_db and llm_model_id:
        #     try:
        #         query_result_id = save_query_to_db(
        #             query=question,
        #             direct_response=clean_answer,
        #             full_response=fullResponse,
        #             llm_model_id=llm_model_id,
        #             sql_queries=sql_queries,
        #             token_usage=token_usage,
        #         )
        #         logger.info(f"Query saved to database with model ID: {llm_model_id}, query_result_id: {query_result_id}")
        #     except Exception as db_error:
        #         logger.error(f"Failed to save query to database: {str(db_error)}")
        #         # Don't raise here, just log the error and continue

        # Return the results
        return {
            "content": clean_answer,
            "full_response": fullResponse,
            "sql_queries": sql_queries,
            "token_usage": token_usage,
            "query_result_id": query_result_id,
            "tool_calls": tool_calls_list,
        }
        
    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        logger.error(error_message)
        return {"error": error_message, "content": f"Error: {str(e)}"}
