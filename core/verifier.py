import logging
from core.models import Task, VerificationResult

logger = logging.getLogger(__name__)

class Verifier:
    """
    Checks whether the Executor's output satisfies the task's success_conditions.
    Checks for unexpected side-effects.
    """
    
    def verify(self, task: Task, result: dict) -> VerificationResult:
        logger.info(f"Verifying task {task.id}")
        
        # Placeholder for actual condition parsing and evaluation
        conditions_met = []
        conditions_failed = []
        
        success = True
        
        if result.get("exit_code") != 0:
            success = False
            conditions_failed.append("exit_code == 0")
        else:
            conditions_met.append("exit_code == 0")
            
        return VerificationResult(
            task_id=task.id,
            success=success,
            success_conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            side_effects=[],
            finding_created=False,
            next_action="continue" if success else "retry"
        )
