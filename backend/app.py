import json
import os
from pathlib import Path
from flask import Flask, request, jsonify
import utils.duck 
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

load_dotenv()  # Load environment variables (for OpenAI API key, etc.)

from typing import Optional, List
from pathlib import Path

from textwrap import dedent

from agno.agent import Agent, Message, RunResponse
from agno.tools.duckdb import DuckDbTools
from agno.utils.log import logger  

class CustomDuckDbTools(DuckDbTools):
    def __init__(self, data_dir, semantic_model=None, **kwargs):
        super().__init__(**kwargs)
        self.data_dir = data_dir
        self.semantic_model = semantic_model
        
    def create_table_from_path(self, path: str, table: Optional[str] = None, replace: bool = False) -> str:
        """Creates a table from a path, using the local data directory

        :param path: Path to load
        :param table: Optional table name to use
        :param replace: Whether to replace the table if it already exists
        :return: Table name created
        """
        original_path = path
        original_table = table
        
        # If we have a semantic model, try to find the correct path for the table
        if self.semantic_model and table:
            # Look for the table in the semantic model
            table_found = False
            for t in self.semantic_model.get('tables', []):
                table_name = t.get('name')
                normalized_table_name = table_name.replace('-', '_')
                
                if table_name == table or normalized_table_name == table:
                    # Use the path from the semantic model
                    path = t.get('path')
                    logger.info(f"Using path from semantic model for table {table}: {path}")
                    table_found = True
                    break
            
            # If table wasn't found but looks like a normalized name, try to find the original
            if not table_found and table.endswith('_info'):
                base_name = table[:-5]  # Remove '_info' suffix
                for t in self.semantic_model.get('tables', []):
                    if t.get('name') == f"{base_name}-info":
                        path = t.get('path')
                        logger.info(f"Using path from semantic model for table {table} (matched to {t.get('name')}): {path}")
                        break
        
        # Special case for ferries_info -> ferries.json
        if table == 'ferries_info' and path == 'ferries-info':
            path = 'ferries.json'
            logger.info(f"Special case: Using ferries.json for ferries_info table")
        
        # Check if path already contains 'data/' prefix and remove it to avoid duplication
        if path.startswith('data/'):
            path = path[5:]  # Remove 'data/' prefix
            
        # Convert the path to an absolute path using the data directory
        absolute_path = os.path.join(self.data_dir, path)
        
        # Check if the file exists
        if not os.path.exists(absolute_path):
            logger.warning(f"File not found: {absolute_path}")
            # Try with .json extension
            if not absolute_path.endswith('.json'):
                json_path = absolute_path + '.json'
                if os.path.exists(json_path):
                    absolute_path = json_path
                    logger.info(f"Found JSON file: {absolute_path}")
        
        if table is None:
            table = self.get_table_name_from_path(path)

        logger.debug(f"Creating table {table} from {absolute_path}")
        create_statement = "CREATE TABLE IF NOT EXISTS"
        if replace:
            create_statement = "CREATE OR REPLACE TABLE"

        create_statement += f" '{table}' AS SELECT * FROM '{absolute_path}';"
        return self.run_query(create_statement)

app = Flask(__name__)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get OpenAI API Key
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


cwd = Path(__file__).parent.resolve()  # Current working directory
data_dir = cwd.joinpath("data")  # Directory for data files
if not data_dir.exists():
    data_dir.mkdir(parents=True)

# Create output directory for saving query results
output_dir = cwd.joinpath("output")
if not output_dir.exists():
    output_dir.mkdir(parents=True)

# --- Helper Functions ---
def load_json_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")  # More informative message
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Error loading JSON from file {filepath}: {e}")  # Include filepath
        return None

def load_prompt_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading prompt from file: {e}")
        return None

def save_response_to_file(question, response, sql_queries=None):
    """Save the query and response to a timestamped file in the output directory
    
    Args:
        question: The original question asked
        response: The response from the agent
        sql_queries: List of SQL queries executed (optional)
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.txt"
    filepath = output_dir.joinpath(filename)
    
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

# --- Agent Initialization ---

semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
if semantic_model_data is None:
    print("Error: Could not load semantic model. Exiting.")
    exit()
semantic_instructions = utils.duck.get_default_instructions(semantic_model_data)

# Create a custom DuckDbTools that uses local paths
duck_tools = CustomDuckDbTools(data_dir=str(data_dir), semantic_model=semantic_model_data)

data_analyst = Agent(  
    instructions=semantic_instructions,
    tools=[duck_tools],
    show_tool_calls=False,
    model=OpenAIChat(id="gpt-4o"), # or gpt-3.5-turbo if you prefer
    markdown=True
)

# --- Flask Routes ---
@app.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})

@app.route("/query", methods=["GET", "POST"])
def query_endpoint():
    data = request.get_json()
    prompt_filepath = data.get("prompt_file", None) # Changed back to prompt_file

    if prompt_filepath:
        question = load_prompt_from_file(data_dir.joinpath(prompt_filepath)) # Path relative to data_dir
        if question is None:
            return jsonify({"error": "Prompt file not found or error reading"}), 400
    else:
        question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question or prompt file provided"}), 400

    try:
        # Set up to capture SQL queries
        sql_queries = []
        
        # Create a function to capture SQL queries
        def query_callback(query):
            sql_queries.append(query)
            return query
        
        # Set the callback on the DuckDbTools instance
        original_run_query = duck_tools.run_query
        duck_tools.run_query = lambda query: original_run_query(query_callback(query))
        
        # Run the agent
        response: RunResponse = data_analyst.run(question)
        
        # Restore original run_query method
        duck_tools.run_query = original_run_query
        
        txt = response.content   
        print(txt)
        
        # Save the query and response to a file, including SQL queries
        saved_filepath = save_response_to_file(question, txt, sql_queries)
        if saved_filepath:
            print(f"Query and response saved to: {saved_filepath}")
            return jsonify({"response": txt, "saved_to": str(saved_filepath)})
        else:
            print("Failed to save query and response to file")
            return jsonify({"response": txt, "saved_to": None})

    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)