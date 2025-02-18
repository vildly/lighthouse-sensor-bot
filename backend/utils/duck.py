from typing import List

def get_default_instructions(semantic_model) -> List[str]:
        instructions = []

        instructions += [
            "Determine if you can answer the question directly or if you need to run a query to accomplish the task.",
            "If you need to run a query, **FIRST THINK** about how you will accomplish the task and then write the query.",
        ]

        if semantic_model is not None:
            instructions += [
                "Using the `semantic_model` below, find which tables and columns you need to accomplish the task.",
            ]

        
        instructions += [
            "If you need to run a query, run `show_tables` to check the tables you need exist.",
            "If the tables do not exist, RUN `create_table_from_path` to create the table using the path from the `semantic_model` or the `knowledge_base`.",
            "Once you have the tables and columns, create one single syntactically correct DuckDB query.",
        ]
        if semantic_model is not None:
            instructions += [
                "If you need to join tables, check the `semantic_model` for the relationships between the tables.",
                "If the `semantic_model` contains a relationship between tables, use that relationship to join the tables even if the column names are different.",
            ]
        
        instructions += [
                "Use 'describe_table' to inspect the tables and only join on columns that have the same name and data type.",
        ]

        instructions += [
            "Inspect the query using `inspect_query` to confirm it is correct.",
            "If the query is valid, RUN the query using the `run_query` function",
            "Analyse the results and return the answer to the user.",
            "If the user wants to save the query, use the `save_contents_to_file` function.",
            "Remember to give a relevant name to the file with `.sql` extension and make sure you add a `;` at the end of the query."
            + " Tell the user the file name.",
            "Continue till you have accomplished the task.",
            "Show the user the SQL you ran",
        ]

    
        return instructions