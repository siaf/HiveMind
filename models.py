from pydantic import BaseModel, Field, field_validator
from typing import Literal, Union, List, Dict, Set
from dataclasses import dataclass
from abc import ABC

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
    available_tools: Dict[str, str] = Field(default_factory=dict)
    available_agents: Dict[str, str] = Field(default_factory=dict)
    verbose: bool = False

class Task(BaseModel, ABC):
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
    task_type: Literal["tool", "agent"] = Field(
        ...,
        description="Type of task - either a tool task or an agent task"
    )
    owner_agent: str = Field(
        default="",
        description="Name of the agent that owns this task"
    )

    @property
    def name(self) -> str:
        """Compatibility property that returns the task's title."""
        return self.title

class ToolTask(Task):
    task_type: Literal["tool"] = "tool"
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
        if isinstance(v, dict):
            for key, value in v.items():
                if isinstance(value, str) and ('\\' in value):
                    v[key] = value.replace('\\', '/')
        return v

    @field_validator('tool_name')
    def validate_tool_name(cls, v, values):
        return v

class AgentTask(Task):
    task_type: Literal["agent"] = "agent"
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
        return v

class TaskList(BaseModel):
    activity: str = Field(..., description="The overall activity or goal")
    tasks: List[Union[ToolTask, AgentTask]] = Field(..., description="List of tasks to be executed")

    class Config:
        json_schema_extra = {
            "example": {
                "activity": "Directory Analysis",
                "tasks": [
                    {
                        "title": "List directory contents",
                        "description": "List all files in the current directory",
                        "task_type": "tool",
                        "tool_name": "ls",
                        "tool_params": {}
                    },
                    {
                        "title": "Analyze files",
                        "description": "Analyze the content of all text files",
                        "task_type": "agent",
                        "agent_name": "file_analyzer",
                        "instructions": "Read and analyze all text files in the directory"
                    }
                ]
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
                        "task_type": "tool",
                        "tool_name": "ls",
                        "tool_params": {}
                    }
                ]
            }
        }