import json
import os
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
import utils.duck 
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import io
import logging
from contextlib import redirect_stdout
from app.services.query import query

load_dotenv()  # Load environment variables (for OpenAI API key, etc.)

from typing import Optional, List
from pathlib import Path

from textwrap import dedent

from agno.agent import Agent, Message, RunResponse
from agno.tools.duckdb import DuckDbTools
from agno.utils.log import logger 

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})

@api_bp.route("/query", methods=["GET", "POST"])
def query_endpoint():
    data = request.get_json()
    
    # Get the necessary objects from app config
    data_analyst = current_app.config['DATA_ANALYST']
    data_dir = current_app.config['DATA_DIR']
    output_dir = current_app.config['OUTPUT_DIR']
    
    # Call the query service
    result = query(
        data=data, 
        data_dir=data_dir, 
        output_dir=output_dir, 
        data_analyst=data_analyst
    )
    
    # Check if result is a tuple (response, status_code)
    if isinstance(result, tuple) and len(result) == 2:
        return jsonify(result[0]), result[1]
    
    # Otherwise, just return the result
    return jsonify(result)

@api_bp.route("/test", methods=["GET"])
def test_connection():
    """Test endpoint to verify the connection between frontend and backend"""
    return jsonify({
        "content": "Backend connection test successful",
        "status": "online"
    })

 