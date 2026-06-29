import logging
from datetime import datetime
from core.models import Observation, Thought, Task, VerificationResult
from core.planner import Planner
from core.executor import Executor
from core.verifier import Verifier
from core.context_manager import ContextManager, TokenOptimizer

logger = logging.getLogger(__name__)

class CognitiveLoop:
    """
    Coordinates the OBSERVE -> THINK -> PLAN -> EXECUTE -> VERIFY -> LEARN cycle.
    """
    def __init__(self, planner: Planner, executor: Executor, verifier: Verifier, context: ContextManager):
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.context = context
        self.optimizer = TokenOptimizer(context)

    def run_iteration(self, active_task: Task) -> None:
        logger.info(f"Starting cognitive loop iteration for task: {active_task.id}")
        
        # 1. OBSERVE
        observation = self.observe(active_task)
        self.context.working_memory.append(observation)
        
        # 2. THINK
        thought = self.think(observation, active_task)
        
        # 3. PLAN
        # In this implementation, planner generates tasks if hypotheses suggest new paths
        # Usually replan happens based on findings or specific thoughts.
        if thought.selected_hypothesis:
            new_tasks = self.planner.replan(findings=[], graph=None)
            # tasks would be enqueued in a real system
            
        # 4. EXECUTE
        result = self.executor.run(active_task)
        
        # 5. VERIFY
        verification = self.verifier.verify(active_task, result)
        
        # 6. LEARN
        self.learn(active_task, verification)

    def observe(self, task: Task) -> Observation:
        logger.debug("Cognitive Step: OBSERVE")
        return Observation(
            timestamp=datetime.utcnow(),
            source="memory",
            raw_output="Observation placeholder",
            parsed={},
            scope_violations=[],
            token_count=10
        )

    def think(self, observation: Observation, task: Task) -> Thought:
        logger.debug("Cognitive Step: THINK")
        prompt = self.context.build_prompt("THINK", task)
        # Placeholder for LLM call
        return Thought(
            observation_id="obs-1",
            interpretation="Placeholder interpretation",
            hypotheses=["Continue execution"],
            risks=["None"],
            escalation_needed=False,
            selected_hypothesis="Continue execution",
            confidence=0.9
        )

    def learn(self, task: Task, verification: VerificationResult) -> None:
        logger.debug("Cognitive Step: LEARN")
        # 1. Extract findings
        # 2. Update knowledge graph
        # 3. Embed summary
        # 4. Optimize memory
        self.optimizer.compress_working_memory()
        
        # 5. Emit events & commit
        if verification.success:
            logger.info(f"Task {task.id} succeeded. Learning phase complete.")
        else:
            logger.warning(f"Task {task.id} failed verification.")
