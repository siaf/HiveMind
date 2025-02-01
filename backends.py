import os
from typing import List
import json
import openai
import requests
from models import Message

class LLMBackend:
    def generate_response(self, messages: List[Message]) -> str:
        raise NotImplementedError

class OpenAIBackend(LLMBackend):
    def __init__(self, model_name: str):
        self.model_name = model_name
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def generate_response(self, messages: List[Message]) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=[{"role": msg.role, "content": msg.content} for msg in messages]
        )
        return response.choices[0].message.content

class OllamaBackend(LLMBackend):
    def __init__(self, model_name: str = "deepseek-r1:14b"):
        self.model_name = model_name
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def generate_response(self, messages: List[Message]) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages]
            },
            stream=True
        )
        
        # Process the streaming response
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    response_json = json.loads(line.decode('utf-8'))
                    # Check for both 'response' and 'message' fields as per Ollama API format
                    chunk = ""
                    if "response" in response_json:
                        chunk = response_json["response"]
                    elif "message" in response_json and "content" in response_json["message"]:
                        chunk = response_json["message"]["content"]
                    
                    if chunk:
                        print(chunk, end='', flush=True)
                        full_response += chunk
                except json.JSONDecodeError:
                    continue
        
        print()  # Add a newline at the end of the response
        
        if full_response:
            return full_response
        raise ValueError("No valid response received from Ollama API")