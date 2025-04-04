from flask import Blueprint, request, jsonify, current_app
from app.helpers.load_json_from_file import load_json_from_file
from dotenv import load_dotenv
from app.services.query import query
from app.conf.CustomDuckDbTools import CustomDuckDbTools

load_dotenv()
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})

@api_bp.route("/query", methods=["GET", "POST"])
def query_endpoint():
    data = request.get_json()
    
    # Get the necessary objects from app config
    data_dir = current_app.config['DATA_DIR']
    output_dir = current_app.config['OUTPUT_DIR']
    
    # Get source_file from request if provided
    source_file = data.get('source_file')
    
    if not source_file:
        return jsonify({"error": "Source file is required"}), 400
    
    # Get model_id from request if provided
    llm_model_id = data.get('llm_model_id') 
    
    if not llm_model_id:
        return jsonify({"error": "LLM Model ID is required"}), 400
    
    # If source_file is provided, create a new agent with the source_file
    if source_file:
        semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
        if semantic_model_data is None:
            print("Error: Could not load semantic model. Exiting.")
            exit()
    
        # Create a new instance of CustomDuckDbTools with the source_file
        duck_tools = CustomDuckDbTools(
            data_dir=str(data_dir),
            semantic_model=current_app.config['SEMANTIC_MODEL'],
            source_file=source_file
        )
        
        # Initialize a new agent for this request with the custom tools
        from app.services.agent import initialize_agent
        data_analyst = initialize_agent(data_dir, llm_model_id, [duck_tools])
        
        # Add source file specific instructions
        additional_instructions = [
            f"IMPORTANT: Use the file '{source_file}' as your primary data source.",
            f"When you need to create a table, use 'data' as the table name and it will automatically use the file '{source_file}'."
        ]
        data_analyst.instructions = data_analyst.instructions + additional_instructions
    
    # Call the query service
    return query(
        data=data, 
        data_dir=data_dir,
        data_analyst=data_analyst
    )

@api_bp.route("/test", methods=["GET"])
def test_connection():
    """Test endpoint to verify the connection between frontend and backend"""
    return jsonify({
        "content": "Backend connection test successful",
        "status": "online"
    })

 