from pydantic import BaseModel, Field, field_validator
from typing import Literal, Union, List, Dict, Set
from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str
    name: str

@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    backend: Literal["openai", "ollama"]
    model_name: str
    available_tools: Set[str] = Field(default_factory=set)
    available_agents: Set[str] = Field(default_factory=set)
    verbose: bool = False

class Task(BaseModel):
    title: str = Field(
        ...,
        description="The title of the task",
        min_length=3,
        examples=["Implement user authentication", "Design database schema"],
        json_schema_extra={"examples": ["Set up API endpoints", "Create user interface"]}
    )
    description: str = Field(
        ...,
        description="Detailed description of what needs to be done",
        min_length=10,
        examples=["Set up JWT-based authentication system", "Design and implement database schema"]
    )
    estimated_duration: str = Field(
        ...,
        description="Estimated time to complete the task",
        pattern=r'^\d+\s*(hour|hours|minute|minutes|day|days)$',
        examples=["2 hours", "1 day", "30 minutes"],
        json_schema_extra={"examples": ["4 hours", "45 minutes", "2 days"]}
    )
    task_type: Literal["tool", "agent"] = Field(
        ...,
        description="Type of task - either a tool task or an agent task"
    )

class ToolTask(Task):
    tool_name: str = Field(
        ...,
        description="Name of the tool to be executed"
    )
    tool_params: Dict = Field(
        default_factory=dict,
        description="Parameters for the tool execution"
    )

    @field_validator('tool_params')
    def normalize_paths(cls, v):
        # Normalize any file paths in the parameters
        if isinstance(v, dict):
            for key, value in v.items():
                if isinstance(value, str) and ('\\' in value):
                    v[key] = value.replace('\\', '/')
        return v

    @field_validator('tool_name')
    def validate_tool_name(cls, v, values):
        # This will be validated against available_tools in the agent config
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "List directory contents",
                "description": "List all files in the current directory",
                "estimated_duration": "5 minutes",
                "task_type": "tool",
                "tool_name": "ls",
                "tool_params": {}
            }
        }

class AgentTask(Task):
    agent_name: str = Field(
        ...,
        description="Name of the subordinate agent to handle this task"
    )
    instructions: str = Field(
        ...,
        description="Detailed instructions for the subordinate agent",
        min_length=20
    )

    @field_validator('agent_name')
    def validate_agent_name(cls, v, values):
        # This will be validated against available_agents in the agent config
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Analyze text files",
                "description": "Read and summarize text files in the directory",
                "estimated_duration": "10 minutes",
                "task_type": "agent",
                "agent_name": "text_analyzer",
                "instructions": "Read each text file in the directory and provide a one-sentence summary of its contents"
            }
        }

class TaskBreakdown(BaseModel):
    activity: str = Field(
        ...,
        description="The main activity or category for the tasks",
        min_length=5,
        examples=["Backend Development", "Frontend Implementation", "System Architecture"]
    )
    tasks: List[Union[ToolTask, AgentTask]] = Field(
        ...,
        description="List of tasks under this activity",
        min_items=1
    )

    @field_validator('tasks')
    def validate_tasks(cls, v):
        if not v:
            raise ValueError('At least one task is required')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "activity": "Directory Analysis",
                "tasks": [
                    {
                        "title": "List directory contents",
                        "description": "List all files in the specified directory",
                        "estimated_duration": "5 minutes",
                        "task_type": "tool",
                        "tool_name": "ls",
                        "tool_params": {}
                    }
                ]
            }
        }