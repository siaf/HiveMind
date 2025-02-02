import os
import warnings
warnings.filterwarnings("ignore", category=Warning, module="urllib3")
from dotenv import load_dotenv
import argparse
from agent import AgentConfig
from models import TaskBreakdown, AgentModel
from agent import Agent
from task_queue import TaskQueue
import json
from shared_types import AgentState
from workflow import Workflow

# ANSI color codes
COLORS = {
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'BOLD': '\033[1m',
    'END': '\033[0m'
}

def main():
    parser = argparse.ArgumentParser(description='Run the agent to analyze directory contents')
    parser.add_argument('-p', '--path', default='.', help='Path to analyze')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode for detailed output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode for system prompts and message history')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    reminder_for_json_only_prompts = "Reminder that only JSON respones are acceptable as we need to parse them using code. DO NOT INCLUDE ADDITIOAL EXPLANATION OR ANALYSIS."
                                    
    text_analyzer_config = AgentConfig(
        name="text_analyzer",
        description=f"Analyzes text files one at a time, providing detailed content summaries. Cannot process muliple files at once. {reminder_for_json_only_prompts}",
        system_prompt_content="Analyze text files and provide detailed summaries of their contents.",
        backend="ollama",
        model_name="deepseek-r1:14b",
        available_tools={
            "read_file": "Reads the contents of a single text file"
        },
        available_agents={},
        verbose=args.verbose,
        debug=args.debug
    )
    text_analyzer = Agent(text_analyzer_config)
    
# Create agent models
    directory_analyzer_config = AgentConfig(
        name="DirectoryAnalyzer",
        description="Analyzes the specified directory by listing its contents and providing summaries of text files.",
        system_prompt_content=f"Analyze the specified directory by listing its contents and providing summaries of text files. {reminder_for_json_only_prompts}",
        backend="ollama",
        model_name="deepseek-r1:14b",
        available_tools={
            "ls": "List directory contents",
            "cd": "Change current working directory"
        },
        available_agents={
            text_analyzer
        },
        verbose=args.verbose,
        debug=args.debug
    )

    # Initialize agents with their respective configs
    directory_analyzer = Agent(directory_analyzer_config)
   
    # Initialize task queue for text analyzer testing
    task_queue = TaskQueue()
    
    # Initialize workflow with text analyzer for testing
    workflow = Workflow(directory_analyzer, task_queue)

    # Test the text analyzer with a sample file
    workflow.process_queue(f"Analyze the contents of {args.path}")

if __name__ == "__main__":
    main()