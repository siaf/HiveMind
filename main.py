import os
from dotenv import load_dotenv
import argparse
from models import AgentConfig, TaskBreakdown
from agent import Agent
from system_prompts import SystemPrompt
from task_queue import TaskQueue
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
    
    # Initialize task queue
    task_queue = TaskQueue()
    
    # Generate initial directory analysis
    normalized_path = args.path.replace('\\', '/')
    response = agent.generate_response(f"Analyze the contents of {normalized_path}")
    
    try:
        # Clean and escape the response string before parsing
        cleaned_response = response.encode('utf-8').decode('unicode-escape')
        # Parse the response into TaskBreakdown model
        task_breakdown = TaskBreakdown.model_validate_json(cleaned_response)
        
        # Add initial tasks to the queue and set owner agent
        for task in task_breakdown.tasks:
            task.owner_agent = agent.config.name
        task_queue.add_tasks(task_breakdown.tasks)
        
        # Print initial analysis header
        print(f"{COLORS['BOLD']}Directory Analysis:{COLORS['END']}")
        print("-" * 50)
        
        # Process all tasks in the queue
        task_count = 0
        while task_queue.has_pending_tasks() or task_queue.current_task:
            if not task_queue.current_task:
                task = task_queue.get_next_task()
                task_count += 1
                print(f"\n{COLORS['BLUE']}{COLORS['BOLD']}Task {task_count}: {task.title}{COLORS['END']}")
                print(f"{COLORS['CYAN']}Description: {task.description}{COLORS['END']}")
                print(f"{COLORS['CYAN']}Estimated Duration: {task.estimated_duration}{COLORS['END']}")
                print(f"{COLORS['CYAN']}Owner Agent: {task.owner_agent}{COLORS['END']}")
            else:
                task = task_queue.current_task
            
            if task.task_type == "tool":
                print(f"{COLORS['GREEN']}Tool: {task.tool_name}{COLORS['END']}")
                # Execute the tool and process its result
                result = agent.execute_tool(task.tool_name, task.tool_params)
                agent.process_tool_result(task.tool_name, result)
                print(f"{COLORS['GREEN']}Tool Result:\n{result}{COLORS['END']}")
                
                # Generate and process follow-up response
                follow_up_response = agent.generate_response(f"Process the results of {task.tool_name} execution")
                print(f"{COLORS['GREEN']}Follow-up Analysis:\n{follow_up_response}{COLORS['END']}")
                
                # Process any new tasks from the follow-up response
                task_queue.process_follow_up_response(follow_up_response, agent)
            else:
                print(f"{COLORS['YELLOW']}Agent: {task.agent_name}{COLORS['END']}")
                print(f"{COLORS['YELLOW']}Instructions: {task.instructions}{COLORS['END']}")
            
            # Mark current task as completed
            task_queue.complete_current_task()
            
    except Exception as e:
        print(f"{COLORS['RED']}Error parsing response: {str(e)}{COLORS['END']}")
        print(f"{COLORS['RED']}Raw response: {response}{COLORS['END']}")

if __name__ == "__main__":
    main()