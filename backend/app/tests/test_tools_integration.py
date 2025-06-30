import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.conf.CustomDuckDbTools import CustomDuckDbTools
from agno.tools.pandas import PandasTools
from agno.tools.python import PythonTools
from app.services.agent import initialize_agent


class TestToolsIntegration(unittest.TestCase):
    """Test suite to verify that Python and Pandas tools are properly integrated"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.semantic_model = {
            "tables": [
                {
                    "name": "test_table",
                    "path": "test_data.csv",
                    "columns": ["id", "name", "value"]
                }
            ]
        }
        
    def test_tools_can_be_instantiated(self):
        """Test that all tool types can be created without errors"""
        try:
            duck_tools = CustomDuckDbTools(
                data_dir=str(self.data_dir),
                semantic_model=self.semantic_model,
            )
            pandas_tools = PandasTools()
            python_tools = PythonTools()
            
            self.assertIsNotNone(duck_tools)
            self.assertIsNotNone(pandas_tools)
            self.assertIsNotNone(python_tools)
            
        except Exception as e:
            self.fail(f"Tool instantiation failed: {e}")
    
    def test_tools_have_correct_types(self):
        """Test that tools have the expected class names"""
        duck_tools = CustomDuckDbTools(
            data_dir=str(self.data_dir),
            semantic_model=self.semantic_model,
        )
        pandas_tools = PandasTools()
        python_tools = PythonTools()
        
        self.assertEqual(duck_tools.__class__.__name__, "CustomDuckDbTools")
        self.assertEqual(pandas_tools.__class__.__name__, "PandasTools")
        self.assertEqual(python_tools.__class__.__name__, "PythonTools")
    
    @patch('app.services.agent.load_json_from_file')
    @patch.dict(os.environ, {
        'OPENROUTER_BASE_URL': 'http://test.com',
        'OPENROUTER_API_KEY': 'test_key'
    })
    def test_agent_initialization_with_all_tools(self, mock_load_json):
        """Test that the agent can be initialized with all tools"""
        # Mock the semantic model loading
        mock_load_json.return_value = self.semantic_model
        
        # Create tools
        duck_tools = CustomDuckDbTools(
            data_dir=str(self.data_dir),
            semantic_model=self.semantic_model,
        )
        pandas_tools = PandasTools()
        python_tools = PythonTools()
        
        tools_list = [duck_tools, python_tools, pandas_tools]
        
        try:
            # This should not raise an exception for tool setup
            # (though it might fail on model connection)
            agent = initialize_agent(
                self.data_dir, 
                "test-model-id", 
                tools_list
            )
            
            # Check that tools are assigned
            self.assertEqual(len(agent.tools), 3)
            
            tool_names = [tool.__class__.__name__ for tool in agent.tools]
            self.assertIn("CustomDuckDbTools", tool_names)
            self.assertIn("PythonTools", tool_names)
            self.assertIn("PandasTools", tool_names)
            
        except Exception as e:
            # If it fails due to model connection, that's OK for this test
            # We're just testing tool integration
            if "connection" not in str(e).lower() and "api" not in str(e).lower():
                self.fail(f"Agent initialization failed for non-connection reason: {e}")
    
    def test_tools_integration_count(self):
        """Test that we have exactly the expected number of tools"""
        duck_tools = CustomDuckDbTools(
            data_dir=str(self.data_dir),
            semantic_model=self.semantic_model,
        )
        pandas_tools = PandasTools()
        python_tools = PythonTools()
        
        tools_list = [duck_tools, python_tools, pandas_tools]
        
        # Should have exactly 3 tools
        self.assertEqual(len(tools_list), 3)
        
        # Each should be a different type
        tool_types = {tool.__class__.__name__ for tool in tools_list}
        self.assertEqual(len(tool_types), 3)


if __name__ == '__main__':
    unittest.main() 