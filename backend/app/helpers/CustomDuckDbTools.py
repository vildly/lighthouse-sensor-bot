from agno.tools.duckdb import DuckDbTools
from typing import Optional
import os
from agno.utils.log import logger

class CustomDuckDbTools(DuckDbTools):
    def __init__(self, data_dir, semantic_model=None, source_file=None, **kwargs):
        super().__init__(**kwargs)
        self.data_dir = data_dir
        self.semantic_model = semantic_model
        self.source_file = source_file
        
    def create_table_from_path(self, path: str, table: Optional[str] = None, replace: bool = False) -> str:
        """Creates a table from a path, using the local data directory

        :param path: Path to load
        :param table: Optional table name to use
        :param replace: Whether to replace the table if it already exists
        :return: Table name created
        """
        original_path = path
        original_table = table
        
        # If source_file is specified and table is 'data', use the source_file
        if self.source_file and (table == 'data' or table == 'main_data' or table == 'ferry_data'):
            path = self.source_file
            logger.info(f"Using specified source file: {path}")
            
            # If the table is 'ferry_data', keep that name, otherwise use 'data'
            if table != 'ferry_data':
                table = 'data'
                
        # Otherwise, if we have a semantic model, try to find the correct path for the table
        elif self.semantic_model and table:
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
        
        # Special case for ferries_info - always use ferries.json regardless of path
        if table == 'ferries_info' or path == 'ferries-info' or path.startswith('ferries-info.'):
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