from typing import Optional, Dict, Any
from collections import deque
from shared_types import AgentState, Task
from task_queue import TaskQueue

class AgentTaskManager:
    def __init__(self):
        self.task_queue = TaskQueue()
        self.current_state = AgentState.IDLE
        self.executing_task_name: Optional[str] = None
        self.waiting_for_agent_id: Optional[str] = None

    def set_state(self, state: AgentState, **kwargs):
        """Update the agent's state with additional context if needed."""
        self.current_state = state
        if state == AgentState.EXECUTING_TASK:
            self.executing_task_name = kwargs.get('task_name')
        elif state == AgentState.WAITING_FOR_AGENT:
            self.waiting_for_agent_id = kwargs.get('agent_id')
        else:
            self.executing_task_name = None
            self.waiting_for_agent_id = None

    def get_state_context(self) -> Dict[str, Any]:
        """Get the current state with additional context."""
        context = {
            'state': self.current_state.value
        }
        if self.executing_task_name:
            context['task_name'] = self.executing_task_name
        if self.waiting_for_agent_id:
            context['waiting_for_agent'] = self.waiting_for_agent_id
        return context

    def clear_queue(self):
        """Clear the task queue while preserving the current state."""
        self.task_queue = TaskQueue()

    def add_task(self, task: Task):
        """Add a new task to the queue."""
        self.task_queue.add_task(task)

    def get_next_task(self) -> Optional[Task]:
        """Get the next task from the queue."""
        return self.task_queue.get_next_task()

    def complete_current_task(self):
        """Complete the current task and update state."""
        self.task_queue.complete_current_task()
        if not self.task_queue.has_pending_tasks():
            self.set_state(AgentState.IDLE)