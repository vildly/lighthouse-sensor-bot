from pathlib import Path
from agno.utils.log import logger

def save_response_to_file(question, response, output_dir, sql_queries=None):
    """Save the query and response to a timestamped file in the output directory
    
    Args:
        question: The original question asked
        response: The response from the agent
        output_dir: Directory to save the file in
        sql_queries: List of SQL queries executed (optional)
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.txt"
    filepath = Path(output_dir).joinpath(filename)
    
    content = f"QUERY:\n{question}\n\nRESPONSE:\n{response}"
    
    # Add SQL queries if available
    if sql_queries:
        content += "\n\nSQL QUERIES:\n"
        for i, query in enumerate(sql_queries, 1):
            content += f"\n--- Query {i} ---\n{query}\n"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except PermissionError:
        logger.error(f"Permission denied when writing to {filepath}. Check directory permissions.")
        # Try writing to a temporary location instead
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        alt_filepath = temp_dir.joinpath(filename)
        try:
            with open(alt_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved to alternative location: {alt_filepath}")
            return alt_filepath
        except Exception as e:
            logger.error(f"Failed to write to alternative location: {e}")
            return None
    except Exception as e:
        logger.error(f"Error saving response to file: {e}")
        return None