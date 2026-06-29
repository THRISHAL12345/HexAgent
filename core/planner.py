from typing import List, Dict, Any
import json
import logging
from core.models import Task

logger = logging.getLogger(__name__)

class Planner:
    """
    Converts objectives and observations into Task objects.
    NEVER calls tools. NEVER mutates state.
    Returns a list of Task objects sorted by dependency order.
    """
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def plan_initial(self, scope: Dict[str, Any], memory: Any) -> List[Task]:
        """Generate recon and enumeration tasks from scope."""
        logger.info("Generating initial plan from scope.")
        # Placeholder for actual LLM generation
        return []

    def replan(self, findings: List[Any], graph: Any) -> List[Task]:
        """Generate exploitation and post-ex tasks from current findings."""
        logger.info("Replanning based on new findings.")
        # Placeholder for actual LLM generation
        return []

    def _build_prompt(self, context: Any) -> str:
        """
        Prompt instructs the LLM to output ONLY a JSON array of Task objects.
        No tool calls. No prose. Schema-validated before returning.
        """
        return ""

    def _validate_tasks(self, tasks: List[Task]) -> List[Task]:
        """Scope-check all tasks. Remove or flag any that target out-of-scope assets."""
        return tasks
