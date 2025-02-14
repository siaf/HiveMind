from typing import List, Dict, Any, Optional, ForwardRef
from .models import Message, AgentModel
from .backends import LLMBackend, OpenAIBackend, OllamaBackend
from .tools import ToolRegistry
from .shared_types import AgentState, Task
from .system_prompts import SystemPrompt

class AgentConfig:
    def __init__(self, 
    name: str,
    description: str,
    system_prompt_content: str,
    backend: str,
    model_name: str,
    available_tools: Dict[str, str],
    available_agents: List['Agent'],
    verbose: bool = False,
    debug: bool = False):
        # Store the actual agent objects
        self.agent_objects = available_agents
        # Convert agents to name-description dictionary for prompts
        agent_descriptions = {agent.config.name: agent.config.description for agent in available_agents}
        prompt = SystemPrompt(
            content=system_prompt_content,
            available_tools=available_tools,
            available_agents=agent_descriptions
        )
        system_prompt = prompt.generate_prompt()
        self.model = AgentModel(
            name=name,
            system_prompt=system_prompt,
            backend=backend,
            model_name=model_name,
            available_tools=available_tools,
            available_agents=agent_descriptions,
            verbose=verbose,
            debug=debug,
        )
        self.name = self.model.name
        self.description = description
        self.system_prompt = self.model.system_prompt
        self.backend = self.model.backend
        self.model_name = self.model.model_name
        self.available_tools = self.model.available_tools
        self.available_agents = self.model.available_agents
        self.verbose = self.model.verbose
        self.debug = self.model.debug

class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.messages: List[Message] = []
        self.backend = self._create_backend()
        self.tool_registry = ToolRegistry()
        self.state = AgentState.IDLE
        self.current_task: Optional[Task] = None

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
        try:
            # Extract only the JSON portion if mixed with text
            if isinstance(tool_params, str):
                import re
                json_match = re.search(r'\{[^}]*\}', tool_params)
                if json_match:
                    tool_params = json.loads(json_match.group())
            return self.tool_registry.execute_tool(tool_name, tool_params)
        except json.JSONDecodeError as e:
            return f"Error parsing tool parameters: {str(e)}"
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def process_tool_result(self, tool_name: str, result: str) -> None:
        """Process the result of a tool execution and add it to message history."""
        formatted_result = f"=== Tool Execution Result ===\nTool: {tool_name}\nResult:\n{result}\n=== End Result ===\n"
        if self.current_task:
            formatted_result += f"\n=== Task Completion ===\nTask: {self.current_task.name}\nDescription: {self.current_task.description}\nResult: {result}\n=== End Task Completion ==="
        self.add_message(Message(
            role="system",
            content=formatted_result,
            name=self.config.name
        ))
    
    def process_subordinate_agent_result(self, agent_name: str, result: str) -> None:
        """Process the result of a agent workflow execution and add it to message history."""
        formatted_result = f"=== Agent Execution Result ===\nTool: {agent_name}\nResult:\n{result}\n=== End Result ===\n"
        if self.current_task:
            formatted_result += f"\n=== Task Completion ===\nTask: {self.current_task.name}\nDescription: {self.current_task.description}\nResult: {result}\n=== End Task Completion ==="
        self.add_message(Message(
            role="system",
            content=formatted_result,
            name=self.config.name
        ))

    def generate_response(self, prompt: str, task_queue) -> str:
        self.state = AgentState.THINKING
        # Add system prompt if this is the first message
        if not self.messages:
            self.add_message(Message(
                role="system",
                content=self.config.system_prompt,
                name=self.config.name
            ))
        
        # Add completed tasks information if available
        if task_queue.completed_tasks:
            completed_tasks_info = "=== Previously Completed Tasks ===\n"
            for task in task_queue.completed_tasks:
                completed_tasks_info += f"- {task.name}:\n  Description: {task.description}\n"
                if hasattr(task, 'result') and task.result:
                    completed_tasks_info += f"  Result: {task.result}\n"
            completed_tasks_info += "=== End Completed Tasks ===\n"
            self.add_message(Message(
                role="system",
                content=completed_tasks_info,
                name=self.config.name
            ))
        
        # Clear the task queue before generating new response
        task_queue.queue.clear()

        # Add the new message
        self.add_message(Message(
            role="user",
            content=prompt,
            name=self.config.name
        ))
        
        # Print current message history for debugging
        if self.config.verbose and self.config.debug:
            print("\n\033[90m=== Messages being sent to LLM ===\n\033[0m")
            for msg in self.messages:
                print(f"\033[90m[{msg.role}] {msg.name}: {msg.content}\n\033[0m")

        # Generate response
        response = self.backend.generate_response(self.messages)

        # Add the response to message history
        self.add_message(Message(
            role="assistant",
            content=response,
            name=self.config.name
        ))

        return response