from pydantic import BaseModel
from typing import Literal, Union

from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str
    name: str

@dataclass
class AgentConfig:
    name: str
    backend: str
    model_name: str
    system_prompt: str
    verbose: bool = False
    backend: Literal["openai", "ollama"]
    model_name: str