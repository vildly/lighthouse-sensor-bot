# type: ignore
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.pandas import PandasTools
from agno.tools.python import PythonTools
import utils.duck
from app.helpers.load_json_from_file import load_json_from_file
from dotenv import load_dotenv
import os

load_dotenv()


def initialize_agent(data_dir, llm_model_id, tools):
    """Initialize the agent with the necessary tools and configuration

    Args:
        data_dir: Path to the data directory
        llm_model_id: model ID to use for the OpenRouter model
        tools: The list of tools to use (DuckDB, Python, Pandas, etc.)

    Returns:
        The initialized agent
    """
    semantic_model_data = load_json_from_file(data_dir.joinpath("semantic_model.json"))
    if semantic_model_data is None:
        print("Error: Could not load semantic model. Exiting.")
        exit()


    semantic_instructions = utils.duck.get_default_instructions(semantic_model_data)

    standard_system_message = utils.duck.get_system_message(
        semantic_instructions, semantic_model_data
    )

    BASE_URL = os.getenv("OPENROUTER_BASE_URL")
    API_KEY = os.getenv("OPENROUTER_API_KEY")

    data_analyst = Agent(
        instructions=semantic_instructions,
        system_message=standard_system_message,
        tools=tools,
        show_tool_calls=True,
        model=OpenRouter(
            base_url=BASE_URL, api_key=API_KEY, id=llm_model_id
        ),
        tool_choice="auto",
        tool_call_limit=20,
        markdown=True,
    )

    return data_analyst