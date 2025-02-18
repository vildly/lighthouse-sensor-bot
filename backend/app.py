import json
import os
from pathlib import Path
from flask import Flask, request, jsonify
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.tools.duckdb import DuckDbTools  # Import DuckDbTools
from dotenv import load_dotenv

load_dotenv()  # Load environment variables (for OpenAI API key, etc.)

app = Flask(__name__)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get OpenAI API Key
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


cwd = Path(__file__).parent.resolve()  # Current working directory
data_dir = cwd.joinpath("data")  # Directory for data files
if not data_dir.exists():
    data_dir.mkdir(parents=True)


# --- Helper Functions ---
def load_json_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Error loading JSON from file: {e}")
        return None


def load_prompt_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading prompt from file: {e}")
        return None


def initialize_duckdb_tools(filepath):
    # Get the file extension
    file_ext = Path(filepath).suffix.lower()

    # Create appropriate init command based on file type
    if file_ext == ".json":
        init_command = (
            f"CREATE TABLE data AS SELECT * FROM read_json_auto('{filepath}')"
        )
    elif file_ext == ".csv":
        init_command = f"CREATE TABLE data AS SELECT * FROM read_csv_auto('{filepath}')"
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

    return DuckDbTools(init_commands=[init_command])


# --- Flask Routes ---
@app.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})


@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json()
    print("Received data:", data)  # Debug print
    
    question = data.get("question", "")
    filepath = data.get("filepath", None)
    prompt_filepath = data.get("prompt_file", None)

    # Load semantic model
    semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
    if semantic_model_data is None:
        return jsonify({"error": "Could not load semantic model"}), 500

    # Initialize DuckDB tools
    try:
        if filepath:
            file_path = data_dir.joinpath(filepath)
            duckdb_tools = initialize_duckdb_tools(file_path)
        else:
            duckdb_tools = DuckDbTools()

        data_analyst = Agent(
            tools=[duckdb_tools],
            show_tool_calls=True,
            instructions="You are a data analyst. Use the available tools to answer questions about the data.",
            model=OpenAIChat(id="gpt-3.5-turbo"),
            markdown=True,
        )

        if prompt_filepath:
            filepath = data_dir.joinpath(prompt_filepath)
            question = load_prompt_from_file(filepath)
            if question is None:
                return jsonify({"error": "Prompt file not found or error reading"}), 400

        if not question:
            return jsonify({"error": "No question provided"}), 400

        response: RunResponse = data_analyst.run(question)
        txt = response.content
        print(txt)
        return jsonify({"content": txt})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
