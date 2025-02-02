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
        self.requires_approval = False
    
    def _execute(self, params: Dict[str, Any]) -> str:
        # Mock implementation that returns 3 text files
        # Path parameter is optional, defaults to current directory
        path = params.get('path', '.')
        mock_files = [
            'file1.txt',
            'file2.txt',
            'file3.txt'
        ]
        return '\n'.join(mock_files)

class ChangeDirectoryTool(Tool):
    """Tool for changing the current working directory."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = False
    
    def _execute(self, params: Dict[str, Any]) -> str:
        # Mock implementation that simulates directory change
        path = params.get('path', '.')
        return f"Tool Suceeded. Changed directory to {path}"

class CreateFileTool(Tool):
    """Tool for creating a new file with content."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = True
    
    def _execute(self, params: Dict[str, Any]) -> str:
        file_path = params.get('file_path')
        content = params.get('content', '')
        
        if not file_path:
            return "Error: 'file_path' parameter is required"
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully created file: {file_path}"
        except Exception as e:
            return f"Error creating file: {str(e)}"

class CreateFolderTool(Tool):
    """Tool for creating a new folder."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = True
    
    def _execute(self, params: Dict[str, Any]) -> str:
        path = params.get('path')
        
        if not path:
            return "Error: 'path' parameter is required"
        
        try:
            os.makedirs(path, exist_ok=True)
            return f"Successfully created folder: {path}"
        except Exception as e:
            return f"Error creating folder: {str(e)}"

class ReadFileTool(Tool):
    """Tool for reading file contents."""
    
    def __init__(self):
        super().__init__()
        self.requires_approval = False
    
    def _execute(self, params: Dict[str, Any]) -> str:
        file_path = params.get('path') or params.get('file_path')
        if not file_path:
            return "Error: Either 'path' or 'file_path' parameter is required"
        
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        self.register_tool('ls', ListDirectoryTool())
        self.register_tool('cd', ChangeDirectoryTool())
        self.register_tool('read_file', ReadFileTool())
        self.register_tool('create_file', CreateFileTool())
        self.register_tool('create_folder', CreateFolderTool())
    
    def register_tool(self, name: str, tool: Tool, description: Dict[str, str] = None):
        """Register a new tool.
        
        Args:
            name: The name of the tool
            tool: The tool instance
            description: Optional dictionary containing tool parameter descriptions
        """
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