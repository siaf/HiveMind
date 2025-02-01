import os
from dotenv import load_dotenv
import argparse
from models import AgentConfig, TaskBreakdown
from agent import Agent
from system_prompts import SystemPrompt
import json

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

    print(f"\nAnalyzing directory: {args.path}\n")
    
    # Generate directory analysis
    response = agent.generate_response(f"Analyze the contents of {args.path}")
    
    try:
        # Parse the response into TaskBreakdown model
        task_breakdown = TaskBreakdown.model_validate_json(response)
        
        # Print the tasks in a formatted way
        print("Directory Analysis:")
        print("-" * 50)
        for i, task in enumerate(task_breakdown.tasks, 1):
            print(f"\nTask {i}: {task.title}")
            print(f"Description: {task.description}")
            print(f"Estimated Duration: {task.estimated_duration}")
            if task.task_type == "tool":
                print(f"Tool: {task.tool_name}")
            else:
                print(f"Agent: {task.agent_name}")
                print(f"Instructions: {task.instructions}")
            
    except Exception as e:
        print(f"Error parsing response: {str(e)}")
        print("Raw response:", response)

if __name__ == "__main__":
    main()