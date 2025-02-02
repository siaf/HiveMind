from typing import List, Optional, Dict, Any
from collections import deque
from .models import TaskBreakdown, Task, ToolTask, AgentTask
from .agent import Agent

class TaskQueue:
    def __init__(self):
        self.queue = deque()
        self.current_task: Optional[Task] = None
        self.completed_tasks: List[Task] = []

    def add_tasks(self, tasks: List[Task]):
        """Add multiple tasks to the queue."""
        for task in tasks:
            self.queue.append(task)

    def add_task(self, task: Task):
        """Add a single task to the queue."""
        self.queue.append(task)

    def get_next_task(self) -> Optional[Task]:
        """Get the next task from the queue."""
        if not self.queue:
            return None
        self.current_task = self.queue.popleft()
        return self.current_task

    def complete_current_task(self):
        """Mark the current task as completed and move it to completed_tasks."""
        if self.current_task:
            self.completed_tasks.append(self.current_task)
            self.current_task = None

    def has_pending_tasks(self) -> bool:
        """Check if there are any pending tasks in the queue."""
        return len(self.queue) > 0

    MAX_RETRY_ATTEMPTS = 3

    def process_follow_up_response(self, response: str, agent: Agent):
        """Process a follow-up response and add any new tasks to the queue."""
        retry_count = 0
        while retry_count < self.MAX_RETRY_ATTEMPTS:
            try:
                # Clean and escape the response string before parsing
                cleaned_response = response.encode('utf-8').decode('unicode-escape')
                # Parse the response into TaskBreakdown model
                task_breakdown = TaskBreakdown.model_validate_json(cleaned_response)
                # Add new tasks to the queue
                self.add_tasks(task_breakdown.tasks)
                return  # Successfully processed, exit the retry loop
            except Exception as e:
                retry_count += 1
                if retry_count < self.MAX_RETRY_ATTEMPTS:
                    print(f"Error parsing follow-up response (attempt {retry_count}/{self.MAX_RETRY_ATTEMPTS}). Retrying...")
                    response = agent.generate_response(f"Previous response could not be parsed. Please try again with a valid JSON response.", self)
                else:
                    print(f"Error parsing follow-up response after {self.MAX_RETRY_ATTEMPTS} attempts: {str(e)}")