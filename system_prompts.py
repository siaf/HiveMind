from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Set
from typing_extensions import Annotated

class SystemPrompt(BaseModel):
    role: Annotated[str, Field(
        default="system",
        description="The role of the system prompt",
        pattern=r'^system$'
    )]
    content: Annotated[str, Field(
        ...,
        description="The main content of the system prompt",
        min_length=10,
        examples=["Break down this project into detailed tasks", "Create a development plan for this feature"]
    )]
    available_tools: Set[str] = Field(
        default_factory=set,
        description="Set of tool names that can be used in tasks"
    )
    available_agents: Set[str] = Field(
        default_factory=set,
        description="Set of agent names that can be used in tasks"
    )
    examples: List[Dict] = Field(
        default=[
            {
                "activity": "Directory Analysis",
                "tasks": [{
                    "title": "List directory contents",
                    "description": "List all files in the current directory",
                    "estimated_duration": "5 minutes",
                    "task_type": "tool",
                    "tool_name": "ls",
                    "tool_params": {}
                }]
            },
            {
                "activity": "File Analysis",
                "tasks": [{
                    "title": "Analyze text files",
                    "description": "Read and summarize text files in the directory",
                    "estimated_duration": "10 minutes",
                    "task_type": "agent",
                    "agent_name": "text_analyzer",
                    "instructions": "Read each text file and provide a summary"
                }]
            }
        ],
        description="Example responses to guide the model"
    )
    format_instructions: str = Field(
        default="Return your response as a clean JSON object without any markdown formatting. The JSON object should have 'activity' and 'tasks' fields. Tasks can be either tool tasks or agent tasks.",
        description="Instructions for response formatting",
        min_length=20
    )
    response_schema: Dict = Field(
        default={
            "type": "object",
            "properties": {
                "activity": {"type": "string", "minLength": 5},
                "tasks": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "minLength": 3},
                                    "description": {"type": "string", "minLength": 10},
                                    "estimated_duration": {"type": "string", "pattern": "^\\d+\\s*(hour|hours|minute|minutes|day|days)$"},
                                    "task_type": {"type": "string", "enum": ["tool"]},
                                    "tool_name": {"type": "string"},
                                    "tool_params": {"type": "object"}
                                },
                                "required": ["title", "description", "estimated_duration", "task_type", "tool_name", "tool_params"]
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "minLength": 3},
                                    "description": {"type": "string", "minLength": 10},
                                    "estimated_duration": {"type": "string", "pattern": "^\\d+\\s*(hour|hours|minute|minutes|day|days)$"},
                                    "task_type": {"type": "string", "enum": ["agent"]},
                                    "agent_name": {"type": "string"},
                                    "instructions": {"type": "string", "minLength": 20}
                                },
                                "required": ["title", "description", "estimated_duration", "task_type", "agent_name", "instructions"]
                            }
                        ]
                    },
                    "minItems": 1
                }
            },
            "required": ["activity", "tasks"]
        },
        description="JSON schema for validating model responses"
    )

    @field_validator('examples')
    def validate_examples_format(cls, v):
        for example in v:
            if not isinstance(example, dict) or 'activity' not in example or 'tasks' not in example:
                raise ValueError('Each example must be a dictionary with activity and tasks fields')
            if not isinstance(example['tasks'], list):
                raise ValueError('Tasks must be a list')
            for task in example['tasks']:
                if not all(k in task for k in ('title', 'description', 'estimated_duration', 'task_type')):
                    raise ValueError('Each task must have title, description, estimated_duration, and task_type fields')
                if task['task_type'] == 'tool' and not all(k in task for k in ('tool_name', 'tool_params')):
                    raise ValueError('Tool tasks must have tool_name and tool_params fields')
                if task['task_type'] == 'agent' and not all(k in task for k in ('agent_name', 'instructions')):
                    raise ValueError('Agent tasks must have agent_name and instructions fields')
        return v

    def generate_prompt(self) -> str:
        """Generate the complete system prompt string with enhanced structure."""
        sections = [
            f"You are a task planning assistant. {self.content}",
            "Available tools: " + ", ".join(sorted(self.available_tools)),
            "Available agents: " + ", ".join(sorted(self.available_agents)),
            f"IMPORTANT: {self.format_instructions} When providing file paths in responses, use forward slashes (/) instead of backslashes (\\) for cross-platform compatibility.",
            "Response Schema:",
            str(self.response_schema),
            "Example outputs:"
        ]
        
        for example in self.examples:
            sections.append(str(example))
            
        return "\n\n".join(sections)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "role": "system",
                    "content": "Break down this project into detailed development tasks",
                    "format_instructions": "Return a JSON object with activity and tasks fields",
                    "examples": [{
                        "activity": "System Architecture",
                        "tasks": [{
                            "title": "Design system components",
                            "description": "Create detailed architecture diagrams and component specifications",
                            "estimated_duration": "4 hours"
                        }]
                    }]
                }
            ]
        }