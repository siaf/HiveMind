import os
from dotenv import load_dotenv
import argparse
from models import AgentConfig, TaskBreakdown
from agent import Agent
from system_prompts import SystemPrompt
import json

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
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Create system prompt
    system_prompt = SystemPrompt(
        content="Analyze the specified directory by listing its contents and providing summaries of text files.",
        available_tools={"ls", "cd"},
        available_agents={"text_analyzer"}
    )

    # Create agent configuration
    agent_config = AgentConfig(
        name="DirectoryAnalyzer",
        system_prompt=system_prompt.generate_prompt(),
        backend="ollama",
        model_name="deepseek-r1:14b",
        available_tools={"ls", "cd"},
        available_agents={"text_analyzer"},
        verbose=args.verbose
    )

    # Initialize agent
    agent = Agent(agent_config)

    print(f"\nAnalyzing directory: {COLORS['BOLD']}{args.path}{COLORS['END']}\n")
    
    # Generate directory analysis
    # Normalize path for JSON encoding
    normalized_path = args.path.replace('\\', '/')
    response = agent.generate_response(f"Analyze the contents of {normalized_path}")
    
    try:
        # Clean and escape the response string before parsing
        cleaned_response = response.encode('utf-8').decode('unicode-escape')
        # Parse the response into TaskBreakdown model
        task_breakdown = TaskBreakdown.model_validate_json(cleaned_response)
        
        # Print the tasks in a formatted way
        print(f"{COLORS['BOLD']}Directory Analysis:{COLORS['END']}")
        print("-" * 50)
        for i, task in enumerate(task_breakdown.tasks, 1):
            print(f"\n{COLORS['BLUE']}{COLORS['BOLD']}Task {i}: {task.title}{COLORS['END']}")
            print(f"{COLORS['CYAN']}Description: {task.description}{COLORS['END']}")
            print(f"{COLORS['CYAN']}Estimated Duration: {task.estimated_duration}{COLORS['END']}")
            
            if task.task_type == "tool":
                print(f"{COLORS['GREEN']}Tool: {task.tool_name}{COLORS['END']}")
                # Execute the tool and process its result
                result = agent.execute_tool(task.tool_name, task.tool_params)
                agent.process_tool_result(task.tool_name, result)
                print(f"{COLORS['GREEN']}Tool Result:\n{result}{COLORS['END']}")
                # Generate a follow-up response based on the tool result
                follow_up_response = agent.generate_response(f"Process the results of {task.tool_name} execution")
                print(f"{COLORS['GREEN']}Follow-up Analysis:\n{follow_up_response}{COLORS['END']}")
            else:
                print(f"{COLORS['YELLOW']}Agent: {task.agent_name}{COLORS['END']}")
                print(f"{COLORS['YELLOW']}Instructions: {task.instructions}{COLORS['END']}")
            
    except Exception as e:
        print(f"{COLORS['RED']}Error parsing response: {str(e)}{COLORS['END']}")
        print(f"{COLORS['RED']}Raw response: {response}{COLORS['END']}")

if __name__ == "__main__":
    main()