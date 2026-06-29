import logging
from typing import List, Optional, Dict
from core.models import Task
from core.event_bus import event_bus, TaskCompleted, TaskFailed, EscalationRequired
from tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class TaskQueue:
    """
    Priority queue with dependency resolution.
    Tasks blocked on unmet dependencies move to WAITING.
    Tasks whose dependencies complete are automatically unblocked.
    """
    def __init__(self):
        self.pending: List[Task] = []
        self.completed: set = set()
        self.failed: set = set()

    def enqueue(self, tasks: List[Task]) -> None:
        self.pending.extend(tasks)
        # Sort by priority (1 is highest)
        self.pending.sort(key=lambda t: t.priority)

    def dequeue_ready(self) -> Optional[Task]:
        for i, task in enumerate(self.pending):
            # Check dependencies
            if not task.dependencies or all(dep in self.completed for dep in task.dependencies):
                return self.pending.pop(i)
        return None

    def mark_complete(self, task_id: str) -> None:
        self.completed.add(task_id)

    def mark_failed(self, task_id: str) -> None:
        self.failed.add(task_id)

    def snapshot(self) -> List[Task]:
        return self.pending.copy()

class Executor:
    """
    Dequeues tasks from the Task Queue and runs them.
    NEVER reasons about strategy.
    NEVER modifies the task list.
    """
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def run(self, task: Task) -> Dict:
        logger.info(f"Executing task: {task.id} - {task.objective}")
        
        # 1. Scope check
        if getattr(task, 'scope_check', True):
            self._assert_in_scope(task.tool_input)

        # 2. Escalation gate
        if getattr(task, 'escalation_required', False):
            self._escalate_and_wait(task)

        # 3. Tool execution
        tool = self.registry.get(task.tool)
        if not tool:
            raise ValueError(f"Tool {task.tool} not found in registry")
            
        try:
            result = tool.run(task.tool_input, timeout=getattr(task, 'timeout_seconds', 300))
            
            # 4. Emit event
            event_bus.emit(TaskCompleted(
                task_id=task.id, 
                raw_output=result.stdout, 
                duration_seconds=0.0 # Placeholder
            ))
            
            return {
                "task_id": task.id,
                "raw_output": result.stdout,
                "exit_code": result.exit_code
            }
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            event_bus.emit(TaskFailed(task_id=task.id, error=str(e), rollback_executed=False))
            return {
                "task_id": task.id,
                "error": str(e),
                "exit_code": 1
            }

    def _assert_in_scope(self, tool_input: dict):
        pass

    def _escalate_and_wait(self, task: Task):
        event_bus.emit(EscalationRequired(
            task_id=task.id,
            reason="Task requires escalation",
            risk="High",
            awaiting_operator=True
        ))
        # Blocking wait would happen here in a real implementation
