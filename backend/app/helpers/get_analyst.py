import logging
import os
from pathlib import Path
from app.helpers.load_json_from_file import load_json_from_file
from app.conf.CustomDuckDbTools import CustomDuckDbTools
from app.services.agent import initialize_agent

logger = logging.getLogger(__name__)

def get_data_analyst(source_file, llm_model_id=None):
    """
    Get a data analyst agent configured for a specific source file.
    
    Args:
        source_file: The source file to use for data analysis
        llm_model_id: The LLM model ID to use
        
    Returns:
        The configured data analyst agent
    """
    try:
        # Get the data directory
        data_dir = Path(os.getenv("DATA_DIR", "data"))
        
        # Load semantic model
        semantic_model_data = load_json_from_file(
            data_dir.joinpath("semantic_model.json")
        )
        if semantic_model_data is None:
            logger.error("Error: Could not load semantic model.")
            raise ValueError("Could not load semantic model")

        # Create a new instance of CustomDuckDbTools with the source_file
        duck_tools = CustomDuckDbTools(
            data_dir=str(data_dir),
            semantic_model=semantic_model_data,
            source_file=source_file,
        )

        # Initialize a new agent for this request with the custom tools
        data_analyst = initialize_agent(data_dir, llm_model_id, [duck_tools])

        # Add source file specific instructions
        additional_instructions = [
            f"IMPORTANT: Use the file '{source_file}' as your primary data source.",
            f"When you need to create a table, use 'data' as the table name and it will automatically use the file '{source_file}'.",
        ]
        data_analyst.instructions = data_analyst.instructions + additional_instructions
        
        return data_analyst
        
    except Exception as e:
        logger.error(f"Error getting data analyst: {e}")
        raise 