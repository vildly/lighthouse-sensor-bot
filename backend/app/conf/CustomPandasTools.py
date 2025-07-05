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
        self.file_path = None
        
        # Pre-load the main data file if source_file is provided
        print(f"Pre-loading source file: {self.source_file}")
        if self.source_file:    
            self._preload_source_file()
        else:
            print("No source file provided")
    
    def _preload_source_file(self):
        """Pre-load the source file as the main dataframe"""
        try:
            # Resolve the file path using data_dir if provided
            file_path = self.source_file
            if self.data_dir and not os.path.isabs(self.source_file):
                # If source_file is relative and we have data_dir, resolve it
                file_path = os.path.join(self.data_dir, self.source_file)
                self.file_path = file_path
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
            print(f"Attempting to load file: {file_path}")
            
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
                print(f"Failed to create dataframe: {result}")
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

    def run_dataframe_operation(self, dataframe_name: str, operation: str, operation_parameters: dict = None) -> str:
        if operation_parameters is None:
            operation_parameters = {}
        
        # Get the dataframe
        dataframe = self.dataframes.get(dataframe_name)
        if dataframe is None:
            return f"Dataframe '{dataframe_name}' not found"
        
        # Check dataframe size and provide helpful guidance
        if len(dataframe) > 1000:
            return f"Dataframe '{dataframe_name}' is large ({len(dataframe)} rows, {len(dataframe.columns)} columns). " \
                   f"Use head(), tail(), describe(), or info() to explore the data safely. " \
                   f"Current operation '{operation}' would send too much data to the AI."
        
        # For safe operations, proceed normally
        if operation in ["head", "tail", "describe", "info"]:
            return super().run_dataframe_operation(dataframe_name, operation, operation_parameters)
        
        # For other operations, check if they would be too large
        if len(dataframe) > 100:  # stricter limit for other operations
            return f"Operation '{operation}' on dataframe '{dataframe_name}' would send too much data. " \
                   f"Try using head(), tail(), or describe() first to explore the data."
        
        return super().run_dataframe_operation(dataframe_name, operation, operation_parameters)

    def create_pandas_dataframe(
        self, dataframe_name: str, create_using_function: str, function_parameters: Dict[str, Any]
    ) -> str:
        if self.file_path:
            dataframe_name = self.file_path
            print(f"Creating dataframe from file: {dataframe_name}")
            df = super().create_pandas_dataframe(dataframe_name, create_using_function, function_parameters)
            print(f"Created dataframe: {df}")
            return df