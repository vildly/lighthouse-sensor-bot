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

from agno.agent import Agent, Message
from agno.tools.duckdb import DuckDbTools

    
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

# --- Agent Initialization ---



semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
if semantic_model_data is None:
    print("Error: Could not load semantic model. Exiting.")
    exit()
semantic_instructions = utils.duck.get_default_instructions(semantic_model_data)

data_analyst = Agent(  
    instructions=semantic_instructions,
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

    #try:
    response: RunResponse = data_analyst.run(question)
    
    txt = response.content   
    print(txt)

    #except Exception as e:
    #    return jsonify({"error": str(e)}), 500

    return jsonify({"response": txt}) 

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)