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

    # Create system prompts for both agents
    directory_analyzer_prompt = SystemPrompt(
        content="Analyze the specified directory by listing its contents and providing summaries of text files.",
        available_tools={
            "ls": "List directory contents",
            "cd": "Change current working directory"
        },
        available_agents={
            "text_analyzer": "Analyzes text files and provides detailed summaries"
        }
    )
    
    text_analyzer_prompt = SystemPrompt(
        content="Analyze text files and provide detailed summaries of their contents.",
        available_tools={
            "read_file": "Reads the contents of a single text file"
        },
        available_agents={}
    )


    da_sysprompmt=directory_analyzer_prompt.generate_prompt();
    print(da_sysprompmt)
    # Create agent configurations
    directory_analyzer_config = AgentConfig(
        name="DirectoryAnalyzer",
        system_prompt=da_sysprompmt,
        backend="ollama",
        model_name="deepseek-r1:14b",
        available_tools={
            "ls": "List directory contents",
            "cd": "Change current working directory"
        },
        available_agents={
            "text_analyzer": "Analyzes text files one at a time, providing detailed content summaries"
        },
        verbose=args.verbose
    )
    
    text_analyzer_config = AgentConfig(
        name="text_analyzer",
        system_prompt=text_analyzer_prompt.generate_prompt(),
        backend="ollama",
        model_name="deepseek-r1:14b",
        available_tools={
            "read_file": "Readss the contents of a single text file"
        },
        available_agents={},
        verbose=args.verbose
    )

    # Initialize agents
    directory_analyzer = Agent(directory_analyzer_config)
    text_analyzer = Agent(text_analyzer_config)

    print(f"\nAnalyzing directory: {COLORS['BOLD']}{args.path}{COLORS['END']}\n")
    
    # Initialize task queue
    task_queue = TaskQueue()
    
    # Generate initial directory analysis
    normalized_path = args.path.replace('\\', '/')
    response = directory_analyzer.generate_response(f"Analyze the contents of {normalized_path}", task_queue)
    
    try:
        # Clean and escape the response string before parsing
        cleaned_response = response.encode('utf-8').decode('unicode-escape')
        # Parse the response into TaskBreakdown model
        task_breakdown = TaskBreakdown.model_validate_json(cleaned_response)
        
        # Add initial tasks to the queue and set owner agent
        for task in task_breakdown.tasks:
            task.owner_agent = directory_analyzer.config.name
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
                print(f"{COLORS['CYAN']}Owner Agent: {task.owner_agent}{COLORS['END']}")
                print(f"{COLORS['CYAN']}Remaining tasks in queue: {len(task_queue.queue)}{COLORS['END']}")
            else:
                task = task_queue.current_task
            
            if task.task_type == "tool":
                print(f"{COLORS['GREEN']}Tool: {task.tool_name} Params: {task.tool_params}{COLORS['END']}")
                # Execute the tool and process its result
                # Determine which agent should execute the tool
                executing_agent = text_analyzer if task.owner_agent == "text_analyzer" else directory_analyzer
                result = executing_agent.execute_tool(task.tool_name, task.tool_params)
                executing_agent.process_tool_result(task.tool_name, result)
                print(f"{COLORS['GREEN']}Tool Result:\n{result}{COLORS['END']}")
                
                # Generate and process follow-up response
                follow_up_response = executing_agent.generate_response(f"Process the results of {task.tool_name} execution", task_queue)
                print(f"{COLORS['GREEN']}Follow-up Analysis:\n{follow_up_response}{COLORS['END']}")
                
                # Process any new tasks from the follow-up response
                task_queue.process_follow_up_response(follow_up_response, executing_agent)
            else:
                print(f"{COLORS['YELLOW']}Agent: {task.agent_name}{COLORS['END']}")
                print(f"{COLORS['YELLOW']}Instructions: {task.instructions}{COLORS['END']}")
                
                # Determine which agent to execute
                executing_agent = text_analyzer if task.agent_name == "text_analyzer" else directory_analyzer
                
                # Generate response from the agent
                agent_response = executing_agent.generate_response(task.instructions, task_queue)
                print(f"{COLORS['YELLOW']}Agent Response:\n{agent_response}{COLORS['END']}")
                
                # Process any new tasks from the agent's response
                task_queue.process_follow_up_response(agent_response, executing_agent)
            
            # Mark current task as completed
            task_queue.complete_current_task()
            
    except Exception as e:
        print(f"{COLORS['RED']}Error parsing response: {str(e)}{COLORS['END']}")
        print(f"{COLORS['RED']}Raw response: {response}{COLORS['END']}")

if __name__ == "__main__":
    main()