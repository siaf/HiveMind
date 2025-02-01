from abc import ABC, abstractmethod
from typing import Dict, Any
import os

class Tool(ABC):
    """Base class for all tools."""
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> str:
        """Execute the tool with given parameters."""
        pass

class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        try:
            path = params.get('path', '.')
            entries = os.listdir(path)
            return '\n'.join(entries)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

class ChangeDirectoryTool(Tool):
    """Tool for changing the current working directory."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        try:
            path = params.get('path', '.')
            os.chdir(path)
            return f"Changed directory to {os.getcwd()}"
        except Exception as e:
            return f"Error changing directory: {str(e)}"

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        self.register_tool('ls', ListDirectoryTool())
        self.register_tool('cd', ChangeDirectoryTool())
    
    def register_tool(self, name: str, tool: Tool):
        """Register a new tool."""
        self._tools[name] = tool
    
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def execute_tool(self, name: str, params: Dict[str, Any]) -> str:
        """Execute a tool by name with given parameters."""
        tool = self.get_tool(name)
        return tool.execute(params)