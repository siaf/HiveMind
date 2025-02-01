from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    EXECUTING_TASK = "executing_task"
    WAITING_FOR_AGENT = "waiting_for_agent"
    WAITING_FOR_APPROVAL = "waiting_for_approval"

@dataclass
class Task:
    name: str
    description: str
    params: Dict[str, Any]
    type: str

@dataclass
class ToolTask(Task):
    tool_name: str

@dataclass
class AgentTask(Task):
    agent_id: str

@dataclass
class TaskBreakdown:
    tasks: List[Task]