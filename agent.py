from typing import List, Dict, Any
from models import Message, AgentConfig
from backends import LLMBackend, OpenAIBackend, OllamaBackend
from tools import ToolRegistry

class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.messages: List[Message] = []
        self.backend = self._create_backend()
        self.tool_registry = ToolRegistry()

    def _create_backend(self) -> LLMBackend:
        if self.config.backend == "openai":
            return OpenAIBackend(self.config.model_name)
        elif self.config.backend == "ollama":
            return OllamaBackend(self.config.model_name, verbose=self.config.verbose)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")

    def add_message(self, message: Message):
        self.messages.append(message)

    def execute_tool(self, tool_name: str, tool_params: Dict[str, Any]) -> str:
        """Execute a tool and return its result."""
        return self.tool_registry.execute_tool(tool_name, tool_params)

    def process_tool_result(self, tool_name: str, result: str) -> None:
        """Process the result of a tool execution and add it to message history."""
        self.add_message(Message(
            role="system",
            content=f"Tool execution result for {tool_name}:\n{result}",
            name=self.config.name
        ))

    def generate_response(self, prompt: str) -> str:
        # Add system prompt if this is the first message
        if not self.messages:
            self.add_message(Message(
                role="system",
                content=self.config.system_prompt,
                name=self.config.name
            ))

        # Add the new message
        self.add_message(Message(
            role="user",
            content=prompt,
            name=self.config.name
        ))

        # Generate response
        response = self.backend.generate_response(self.messages)

        # Add the response to message history
        self.add_message(Message(
            role="assistant",
            content=response,
            name=self.config.name
        ))

        return response