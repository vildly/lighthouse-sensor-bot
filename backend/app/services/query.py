# type: ignore
from app.helpers.load_prompt_from_file import load_prompt_from_file
from app.helpers.save_query_to_file import save_response_to_file
from app.helpers.save_query_to_db import save_query_to_db
import io
import logging
from agno.utils.log import logger
import re
from flask_socketio import emit
from app.conf.websocket import socketio
from app.utils.websocket_logger import WebSocketLogHandler
from app.helpers.extract_answer import extract_answer_for_evaluation


def query(data, data_dir=None, data_analyst=None, source_file=None):
    """Process a query and return the response
    Args:
        data: The request data
        data_dir: Directory containing data files
        output_dir: Directory to save query and response files
        data_analyst: The agent that will process the query
    """
    prompt_filepath = data.get("prompt_file", None)
    source_file = data.get("source_file", None)
    llm_model_id = data.get("llm_model_id", None)

    if prompt_filepath:
        question = load_prompt_from_file(data_dir.joinpath(prompt_filepath))
        if question is None:
            return {
                "error": "Prompt file not found or error reading",
                "content": "Error: Prompt file not found",
            }, 400
    else:
        question = data.get("question", "")

    if not question:
        return {
            "error": "No question or prompt file provided",
            "content": "Error: No question provided",
        }, 400

    # If source_file is provided, add it to the question
    if source_file:
        question = f"{question} (Use data from {source_file})"

    try:
        # Set up to capture SQL queries
        sql_queries = []

        # Set up to capture logger output
        log_capture = io.StringIO()
        log_handler = logging.StreamHandler(log_capture)
        log_handler.setLevel(logging.INFO)
        logger.addHandler(log_handler)
        
        # Add WebSocket log handler
        websocket_handler = WebSocketLogHandler()
        websocket_handler.setLevel(logging.INFO)
        logger.addHandler(websocket_handler)
        
        # Emit event that query processing has started
        try:
            socketio.emit('query_status', {'status': 'started'}, namespace='/query')
        except Exception as e:
            print(f"Error emitting query_status: {e}")

        # Run the agent
        response = data_analyst.run(question)
        
        # Remove the log handlers
        logger.removeHandler(log_handler)
        logger.removeHandler(websocket_handler)
        
        # Emit event that query processing has completed
        try:
            socketio.emit('query_status', {'status': 'completed'}, namespace='/query')
        except Exception as e:
            print(f"Error emitting query_status: {e}")

        # Extract SQL queries from log output
        log_output = log_capture.getvalue()
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

        # Remove duplicates while preserving order
        unique_queries = []
        for query in sql_queries:
            if query not in unique_queries:
                unique_queries.append(query)
        sql_queries = unique_queries

        fullResponse = response.content
        
        clean_answer = extract_answer_for_evaluation(fullResponse)
        
        # Save the query and response to the database if model ID is provided
        if llm_model_id:
            try:
                save_query_to_db(
                    query=question,
                    direct_response=clean_answer,
                    full_response=fullResponse,
                    llm_model_id=llm_model_id,
                    sql_queries=sql_queries,
                )
                logger.info(f"Query saved to database with model ID: {llm_model_id}")
            except Exception as db_error:
                raise ValueError(f"Failed to save query to database: {str(db_error)}")

        return {
            "content": clean_answer,
            "full_response": fullResponse,
            "sql_queries": sql_queries,
        }

    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        print(error_message)
        return {"error": error_message, "content": f"Error: {str(e)}"}, 500
