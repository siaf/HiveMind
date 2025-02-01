import os
from typing import List
import json
import openai
import requests
from models import Message
from threading import Lock

class LLMBackend:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def generate_response(self, messages: List[Message]) -> str:
        raise NotImplementedError

class OpenAIBackend(LLMBackend):
    _initialized = False

    def __init__(self, model_name: str):
        with self._lock:
            if not self._initialized:
                self.model_name = model_name
                openai.api_key = os.getenv("OPENAI_API_KEY")
                self._initialized = True

    def generate_response(self, messages: List[Message]) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=[{"role": msg.role, "content": msg.content} for msg in messages]
        )
        return response.choices[0].message.content

class OllamaBackend(LLMBackend):
    _initialized = False
    _session = None

    @staticmethod
    def _process_response(response: str) -> str:
        """Remove <think> sections from the response."""
        # Find the last </think> tag
        last_think_end = response.rfind('</think>')
        if last_think_end == -1:
            return response
        
        # Return everything after the last </think> tag
        return response[last_think_end + 8:].strip()

    def __init__(self, model_name: str = "deepseek-r1:14b"):
        with self._lock:
            if not self._initialized:
                self.model_name = model_name
                self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                self._session = requests.Session()
                self._initialized = True

    def generate_response(self, messages: List[Message]) -> str:
        try:
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages]
            }
            
            response = self._session.post(
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
                return self._process_response(full_response)
            raise ValueError("No valid response received from Ollama API")
        except Exception as e:
            print(f"\nError: {str(e)}")
            raise

    def __del__(self):
        if self._session:
            self._session.close()