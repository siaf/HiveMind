from abc import ABC, abstractmethod
from typing import Dict, Any
import os

class Tool(ABC):
    """Base class for all tools."""
    
    def __init__(self):
        self.requires_approval = False
    
    def _get_user_approval(self) -> bool:
        """Get user approval for executing the tool."""
        response = input('\033[91mDo you approve this tool execution? (y/n): \033[0m').lower()
        return response == 'y'
    
    def execute(self, params: Dict[str, Any]) -> str:
        """Execute the tool with given parameters."""
        if self.requires_approval and not self._get_user_approval():
            return "Tool execution cancelled by user"
        return self._execute(params)
    
    @abstractmethod
    def _execute(self, params: Dict[str, Any]) -> str:
        """Internal execute method to be implemented by subclasses."""
        pass

class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = True
    
    def _execute(self, params: Dict[str, Any]) -> str:
        try:
            path = params.get('path', '.')
            entries = os.listdir(path)
            return '\n'.join(entries)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

class ChangeDirectoryTool(Tool):
    """Tool for changing the current working directory."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = True
    
    def _execute(self, params: Dict[str, Any]) -> str:
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