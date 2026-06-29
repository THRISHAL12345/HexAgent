import logging
import os
import argparse
import sys

from memory.db import DatabaseManager
from core.state_machine import StateMachine
from core.planner import Planner
from core.executor import Executor, TaskQueue
from core.verifier import Verifier
from core.context_manager import ContextManager
from core.cognitive_loop import CognitiveLoop
from tools.registry import ToolRegistry

from agents.supervisor import SupervisorAgent
from agents.recon.portscan_agent import PortScanAgent
from agents.report_agent import ReportAgent

from observability.metrics import MetricsExporter
from observability.tracing import Tracer

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hexagent")

def main():
    parser = argparse.ArgumentParser(description="HexAgent Autonomous Security Researcher")
    parser.add_argument("--engagement", type=str, required=True, help="Engagement ID (e.g. eng-2025-042)")
    parser.add_argument("--dry-run", action="store_true", help="Initialize the system and exit immediately (for CI/CD testing)")
    args = parser.parse_args()
    
    engagement_id = args.engagement
    logger.info(f"Initializing HexAgent for engagement: {engagement_id}")

    # 1. Observability
    metrics = MetricsExporter()
    metrics.start()
    _ = Tracer()  # Tracer instantiated but unused in this skeletal implementation

    # 2. Database
    os.makedirs(f"workspaces/{engagement_id}", exist_ok=True)
    db = DatabaseManager(f"workspaces/{engagement_id}/findings.db")

    # 3. State Machine & Supervisor
    state_machine = StateMachine(db, engagement_id)
    
    if state_machine.current_state not in ["IDLE", "PLANNING"]:
        logger.info("Attempting crash recovery...")
        state_machine.recover()

    supervisor = SupervisorAgent(state_machine)

    # 4. Tool Registry
    registry = ToolRegistry()

    # 5. Core Cognitive Components
    task_queue = TaskQueue()
    planner = Planner()
    executor = Executor(registry)
    verifier = Verifier()
    context = ContextManager()

    loop = CognitiveLoop(planner, executor, verifier, context)

    # 6. Leaf Agents
    portscan_agent = PortScanAgent(task_queue)
    report_agent = ReportAgent(db, "workspaces")

    # 7. Start Agents (Subscribing to Event Bus)
    supervisor.start()
    portscan_agent.start()
    report_agent.start()

    logger.info("System Initialized. HexAgent is ready.")
    
    if args.dry_run:
        logger.info("Dry run complete. Exiting.")
        return

    # 8. Start loop if in executing mode (In a real implementation, this would be asynchronous/threaded)
    try:
        import time
        # Mock loop execution
        while state_machine.current_state in ["PLANNING", "EXECUTING", "WAITING", "VERIFYING", "REPLANNING"]:
            task = task_queue.dequeue_ready()
            if task:
                loop.run_iteration(task)
            else:
                # If no tasks and we are planning, we'd emit engagement complete, etc.
                if state_machine.current_state == "EXECUTING":
                    state_machine.transition("SUMMARIZING", "queue.empty")
                    state_machine.transition("DONE", "all_phases.complete")
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("HexAgent shutting down gracefully...")
        supervisor.on_shutdown()
        portscan_agent.on_shutdown()
        report_agent.on_shutdown()
    
if __name__ == "__main__":
    main()
