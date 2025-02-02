from typing import List, Dict, Any
from models import TaskBreakdown
from agent import Agent
from task_queue import TaskQueue
from shared_types import AgentState

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

class Workflow:
    def __init__(self, primary_agent: Agent, task_queue: TaskQueue):
        self.primary_agent = primary_agent
        self.task_queue = task_queue
        self.task_count = 0

    def process_queue(self, initial_prompt: str) -> None:
        """Process the task queue starting with an initial prompt."""
        # Print workflow start boundary
        print(f"\n{COLORS['RED']}=== Agent {self.primary_agent.config.name} starting workflow to do: {initial_prompt} ==={COLORS['END']}")
        print("-" * 50)

        # Maximum number of retries for parsing LLM response
        MAX_RETRIES = 3
        retry_count = 0
        
        # Normalize the initial prompt path separators
        initial_prompt = initial_prompt.replace('\\', '/')

        while retry_count < MAX_RETRIES:
            # Generate initial analysis
            self.primary_agent.state = AgentState.THINKING
            print(f"{COLORS['YELLOW']}Agent {self.primary_agent.config.name} is {self.primary_agent.state.value}{COLORS['END']}")
            response = self.primary_agent.generate_response(initial_prompt, self.task_queue)
            
            try:
                # Clean and escape the response string before parsing
                cleaned_response = response.encode('utf-8').decode('unicode-escape')
                # Parse the response into TaskBreakdown model
                task_breakdown = TaskBreakdown.model_validate_json(cleaned_response)

                # Add initial tasks to the queue and set owner agent
                for task in task_breakdown.tasks:
                    task.owner_agent = self.primary_agent.config.name
                self.task_queue.add_tasks(task_breakdown.tasks)


                # Process all tasks in the queue
                while self.task_queue.has_pending_tasks() or self.task_queue.current_task:
                    self._process_next_task()
                
                # If we successfully parsed and processed the response, break the retry loop
                break

            except Exception as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    print(f"{COLORS['YELLOW']}Failed to parse response (attempt {retry_count}/{MAX_RETRIES}). Retrying...{COLORS['END']}")
                else:
                    print(f"{COLORS['RED']}Error parsing response after {MAX_RETRIES} attempts: {str(e)}{COLORS['END']}")
                    print(f"{COLORS['RED']}Raw response: {response}{COLORS['END']}")

    def _process_next_task(self) -> None:
        """Process the next task in the queue."""
        if not self.task_queue.current_task:
            task = self.task_queue.get_next_task()
            self.task_count += 1
            self._print_task_info(task)
        else:
            task = self.task_queue.current_task

        executing_agent = self._get_executing_agent(task)

        if task.task_type == "tool":
            self._execute_tool_task(task, executing_agent)
        elif task.task_type == "agent":
            self._execute_agent_task(task, executing_agent)
        elif task.task_type == "completion":
            print(f"\n{COLORS['RED']}=== Agent {executing_agent.config.name} completed workflow to '{task.title}' with the following results: \n{task.result}{COLORS['END']}")
            # No need to process further tasks after completion
            self.task_queue.queue.clear()

        # Mark current task as completed and update agent state
        self.task_queue.complete_current_task()
        executing_agent.state = AgentState.IDLE

    def _print_task_info(self, task) -> None:
        """Print information about the current task."""
        executing_agent = self._get_executing_agent(task)
        print(f"\n{COLORS['BLUE']}{COLORS['BOLD']}{executing_agent.config.name} has started Task ({self.task_count}): {task.title}. {task.description}. [Queue Size: {len(self.task_queue.queue)}]{COLORS['END']}")
        print(f"{COLORS['YELLOW']}Agent {executing_agent.config.name} is {executing_agent.state.value} [Queue Size: {len(self.task_queue.queue)}]{COLORS['END']}")

    def _get_executing_agent(self, task) -> Agent:
        """Determine which agent should execute the task."""
        # This method should be expanded when more agents are added
        return self.primary_agent

    def _execute_tool_task(self, task, executing_agent: Agent) -> None:
        """Execute a tool task and process its results."""
        print(f"{COLORS['GREEN']}Agent {executing_agent.config.name} is using tool: {task.tool_name} with params: {task.tool_params}, as part of {task.title}{COLORS['END']}")
        
        executing_agent.state = AgentState.EXECUTING_TASK
        print(f"{COLORS['YELLOW']}Agent {executing_agent.config.name} is {executing_agent.state.value} [Queue Size: {len(self.task_queue.queue)}]{COLORS['END']}")
        
        result = executing_agent.execute_tool(task.tool_name, task.tool_params)
        executing_agent.process_tool_result(task.tool_name, result)
        print(f"{COLORS['GREEN']}Tool Result:\n{result}{COLORS['END']}")

        # Mark the task as completed before processing follow-up
        self.task_queue.complete_current_task()

        # Generate and process follow-up response
        executing_agent.state = AgentState.THINKING
        print(f"{COLORS['YELLOW']}Agent {executing_agent.config.name} is {executing_agent.state.value} [Queue Size: {len(self.task_queue.queue)}]{COLORS['END']}")
        
        follow_up_response = executing_agent.generate_response(
            f"Process the results of {task.tool_name} execution",
            self.task_queue
        )
        
        # Process any new tasks from the follow-up response
        self.task_queue.process_follow_up_response(follow_up_response, executing_agent)

    def _execute_agent_task(self, task, executing_agent: Agent) -> None:
        """Execute an agent task and process its results."""
        print(f"{COLORS['YELLOW']}Agent: {task.agent_name}{COLORS['END']}")
        print(f"{COLORS['GREEN']}Agent {executing_agent.config.name} is instructing agent {task.agent_name} to do: {task.instructions}{COLORS['END']}")

        # Find the subordinate agent from the executing agent's available agents
        subordinate_agent = next((agent for agent in executing_agent.config.agent_objects 
                                if agent.config.name == task.agent_name), None)
        
        if not subordinate_agent:
            print(f"{COLORS['RED']}Error: Subordinate agent {task.agent_name} not found{COLORS['END']}")
            return

        # Update executing agent's state to waiting for subordinate
        executing_agent.state = AgentState.WAITING_FOR_AGENT
        print(f"{COLORS['YELLOW']}Agent {executing_agent.config.name} State: Waiting for {subordinate_agent.config.name}{COLORS['END']}")

        # Create a new task queue for the subordinate agent
        subordinate_queue = TaskQueue()
        
        # Create a new workflow instance with the correct subordinate agent
        subordinate_workflow = Workflow(subordinate_agent, subordinate_queue)
        
        # Process the task in the subordinate workflow
        subordinate_workflow.process_queue(task.instructions)
        
        # Get the final results from the subordinate workflow's last task
        if subordinate_queue.completed_tasks:
            final_result = subordinate_queue.completed_tasks[-1].result if hasattr(subordinate_queue.completed_tasks[-1], 'result') else None
            if final_result:
                print(f"{COLORS['GREEN']}Subordinate Agent Final Result:\n{final_result}{COLORS['END']}")
                
                # Process the subordinate agent result
                executing_agent.process_subordinate_agent_result(task.agent_name, final_result)

                # Mark the task as completed before processing follow-up
                self.task_queue.complete_current_task()

                # Generate and process follow-up response
                executing_agent.state = AgentState.THINKING
                print(f"{COLORS['YELLOW']}Agent {executing_agent.config.name} is {executing_agent.state.value} [Queue Size: {len(self.task_queue.queue)}]{COLORS['END']}")
                
                follow_up_response = executing_agent.generate_response(
                    f"Process the results of {task.agent_name} agent execution",
                    self.task_queue
                )
                print(f"{COLORS['GREEN']}Follow-up Analysis:\n{follow_up_response}{COLORS['END']}")

                # Process any new tasks from the follow-up response
                self.task_queue.process_follow_up_response(follow_up_response, executing_agent)
            else:
                print(f"{COLORS['YELLOW']}No final result from subordinate agent{COLORS['END']}")
        else:
            print(f"{COLORS['YELLOW']}No completed tasks from subordinate agent{COLORS['END']}")