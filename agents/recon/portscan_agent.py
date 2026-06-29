import logging
from datetime import datetime
from agents.supervisor import BaseAgent
from core.event_bus import Event, TaskCompleted
from core.models import Task
from core.executor import TaskQueue

logger = logging.getLogger(__name__)

class PortScanAgent(BaseAgent):
    name = "PortScanAgent"
    subscribes_to = [TaskCompleted]

    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue

    def handle(self, event: Event) -> None:
        if isinstance(event, TaskCompleted):
            self._on_task_completed(event)

    def _on_task_completed(self, event: TaskCompleted) -> None:
        # Example logic: if this was an initial host discovery scan, enqueue port scans
        if "recon-host-discovery" in event.task_id:
            logger.info(f"{self.name} processing host discovery results for port scanning...")
            
            # In a real agent, we would parse event.raw_output to find active IPs
            # For demonstration, we create a mock port scan task.
            task = Task(
                id=f"recon-portscan-{event.task_id}",
                parent_id=event.task_id,
                engagement_id="eng-2025-042",
                objective="Discover open ports on active hosts",
                tool="nmap",
                tool_input={
                    "targets": "203.0.113.10",
                    "flags": "-sV -sC -T3"
                },
                dependencies=[],
                priority=2,
                timeout_seconds=600,
                success_conditions=["result.exit_code == 0"],
                expected_output_schema={},
                rollback=None,
                escalation_required=False,
                phase="recon",
                created_at=datetime.utcnow(),
                started_at=None,
                completed_at=None,
                status="pending",
                result=None,
                scope_check=True
            )
            self.task_queue.enqueue([task])
            logger.info(f"{self.name} enqueued port scan task: {task.id}")
