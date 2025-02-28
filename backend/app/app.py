import json
import os
from pathlib import Path
from flask import Flask, request, jsonify
import utils.duck 
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import io
import logging
from contextlib import redirect_stdout

load_dotenv()  # Load environment variables (for OpenAI API key, etc.)
from pathlib import Path

from textwrap import dedent

from agno.agent import Agent, Message, RunResponse
from agno.tools.duckdb import DuckDbTools
from agno.utils.log import logger  

from app.services.agent import initialize_agent

app = Flask(__name__)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Get OpenAI API Key
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Set up directory paths
cwd = Path(__file__).parent.resolve()  # Current working directory
data_dir = cwd.parent.joinpath("data")  # Directory for data files
if not data_dir.exists():
    data_dir.mkdir(parents=True)

# Create output directory for saving query results
output_dir = cwd.parent.joinpath("output")
if not output_dir.exists():
    output_dir.mkdir(parents=True)

# --- Agent Initialization ---
data_analyst, duck_tools = initialize_agent(data_dir)

# --- Register Routes ---
from app.routes.api import api_bp

# Register blueprints
app.register_blueprint(api_bp)

# Pass the necessary objects to the routes
app.config['DATA_ANALYST'] = data_analyst
app.config['DUCK_TOOLS'] = duck_tools
app.config['DATA_DIR'] = data_dir
app.config['OUTPUT_DIR'] = output_dir

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)