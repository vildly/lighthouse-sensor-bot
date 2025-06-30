from typing import Optional, List
from agno.agent import Message
from textwrap import dedent
import json

def get_default_instructions(semantic_model) -> List[str]:
        instructions = []

        instructions += [
            "Determine if you can answer the question directly or if you need to run operations to accomplish the task.",
            "If you need to analyze data, **FIRST THINK** about the best approach and which tools to use.",
        ]

        if semantic_model is not None:
            instructions += [
                "Using the `semantic_model` below, find which tables and columns you need to accomplish the task.",
            ]

        
        instructions += [
            "For SQL operations, run `show_tables` to check the tables you need exist.",
            "If the tables do not exist, RUN `create_table_from_path` to create the table using the path from the `semantic_model`.",
            "For SQL analysis, create syntactically correct DuckDB queries.",
        ]
        if semantic_model is not None:
            instructions += [
                "If you need to join tables, check the `semantic_model` for the relationships between the tables.",
                "If the `semantic_model` contains a relationship between tables, use that relationship to join the tables even if the column names are different.",
            ]
        
        instructions += [
                "Use 'describe_table' to inspect the tables and only join on columns that have the same name and data type.",
                "For complex data analysis, consider using Python or Pandas tools in combination with SQL results.",
                "When appropriate, load data from DuckDB into Pandas for advanced analysis or visualization.",
        ]

        return instructions

def get_system_message(instructions, semantic_model):
    system_message = """You are a senior data analyst with expertise in SQL, Python, and Pandas.

You have access to multiple analysis tools:
- DuckDB for SQL operations and data querying  
- Python for calculations and general programming
- Pandas for advanced data manipulation and analysis

Choose the right tool for each task and combine them when needed for comprehensive analysis.

"""
    
    if instructions:
        system_message += "Instructions:\n"
        for instruction in instructions:
            system_message += f"- {instruction}\n"
        system_message += "\n"
    
    if semantic_model:
        system_message += f"Semantic Model:\n{json.dumps(semantic_model, indent=2)}\n\n"
    
    system_message += """Provide clear explanations of your analysis process and actionable insights from your findings."""
    
    return system_message