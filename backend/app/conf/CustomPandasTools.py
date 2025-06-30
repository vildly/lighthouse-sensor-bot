from agno.tools.pandas import PandasTools
from pathlib import Path
from agno.utils.log import logger
from typing import Any, Dict
import os

class CustomPandasTools(PandasTools):
    def __init__(self, data_dir=None, source_file=None, semantic_model_data=None, **kwargs):
        super().__init__(**kwargs)
        self.data_dir = data_dir
        self.source_file = source_file
        self.semantic_model_data = semantic_model_data
        
        # Pre-load the main data file if source_file is provided
        if self.source_file:
            self._preload_source_file()
    
    def _preload_source_file(self):
        """Pre-load the source file as the main dataframe"""
        try:
            # Resolve the file path using data_dir if provided
            file_path = self.source_file
            if self.data_dir and not os.path.isabs(self.source_file):
                # If source_file is relative and we have data_dir, resolve it
                file_path = os.path.join(self.data_dir, self.source_file)
            
            # Check if the file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return
            
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.csv':
                function_name = 'read_csv'
                params = {'filepath_or_buffer': file_path}
            elif file_extension == '.json':
                function_name = 'read_json'
                params = {'path_or_buf': file_path}
            elif file_extension in ['.xlsx', '.xls']:
                function_name = 'read_excel'
                params = {'io': file_path}
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return
            
            logger.info(f"Attempting to load file: {file_path}")
            
            # Create the main dataframe
            result = self.create_pandas_dataframe(
                dataframe_name="data",
                create_using_function=function_name,
                function_parameters=params
            )
            
            if result == "data":
                logger.info(f"Successfully created main dataframe 'data' from {file_path}")
            else:
                logger.error(f"Failed to create dataframe: {result}")
                return
            
            # Also create with the semantic model name if available
            if self.semantic_model_data and 'tables' in self.semantic_model_data:
                for table in self.semantic_model_data['tables']:
                    table_name = table.get('name', '').replace('-', '_')
                    if table_name and table_name != 'data':
                        # Create another reference with the semantic table name
                        self.dataframes[table_name] = self.dataframes['data'].copy()
                        logger.info(f"Created dataframe reference: {table_name}")
            
            logger.info(f"Pre-loaded source file {file_path} as dataframe 'data'")
            
        except Exception as e:
            logger.error(f"Error pre-loading source file {self.source_file}: {e}") 