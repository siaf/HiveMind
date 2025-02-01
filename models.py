from pydantic import BaseModel
from typing import Literal, Union

class Message(BaseModel):
    content: str
    role: Literal["assistant", "user", "system"]
    name: Union[str, None] = None

class AgentConfig(BaseModel):
    name: str
    system_prompt: str
    backend: Literal["openai", "ollama"]
    model_name: str