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
        with open(filepath, 'r', encoding='utf-8') as f:
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
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading prompt from file: {e}")
        return None

# --- Agent Initialization ---

# Load semantic model from JSON file
semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
if semantic_model_data is None:
    print("Error: Could not load semantic model. Exiting.")
    exit()

data_analyst = Agent(  # Use the base Agent class
    tools=[DuckDbTools()],  # Initialize with DuckDbTools
    show_tool_calls=True,
    instructions="You are a data analyst. Use the available tools to answer questions about the data.",
    model=OpenAIChat(id="gpt-4o"), # or gpt-3.5-turbo if you prefer
    markdown=True,
)


# --- Flask Routes ---
@app.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})

@app.route("/query", methods=["POST"])
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
        response: RunResponse = data_analyst.run(question)
        txt = response.json()  # Assuming you want the JSON response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return txt

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)