from app.helpers.load_prompt_from_file import load_prompt_from_file
from app.helpers.save_query_to_file import save_response_to_file
import io
import logging
from agno.utils.log import logger

def query(data, data_dir=None, output_dir=None, data_analyst=None, source_file=None):
    """Process a query and return the response
    
    Args:
        data: The request data
        data_dir: Directory containing data files
        output_dir: Directory to save query and response files
        data_analyst: The agent that will process the query
    """
    prompt_filepath = data.get("prompt_file", None)
    source_file = data.get("source_file", None)

    if prompt_filepath:
        question = load_prompt_from_file(data_dir.joinpath(prompt_filepath))
        if question is None:
            return {"error": "Prompt file not found or error reading", "content": "Error: Prompt file not found"}, 400
    else:
        question = data.get("question", "")

    if not question:
        return {"error": "No question or prompt file provided", "content": "Error: No question provided"}, 400

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
        
        # Run the agent
        response = data_analyst.run(question)
        
        # Remove the log handler
        logger.removeHandler(log_handler)
        
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
        
        txt = response.content   
        print(txt)
        
        # Save the query and response to a file, including SQL queries
        saved_filepath = save_response_to_file(
            question, 
            txt, 
            output_dir, 
            sql_queries=sql_queries,
        )
        
        if saved_filepath:
            print(f"Query and response saved to: {saved_filepath}")
            return {"response": txt, "content": txt, "saved_to": str(saved_filepath)}
        else:
            print("Failed to save query and response to file")
            return {"response": txt, "content": txt, "saved_to": None}

    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        print(error_message)
        return {"error": error_message, "content": f"Error: {str(e)}"}, 500