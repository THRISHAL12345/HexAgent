import logging
from abc import ABC, abstractmethod
from core.event_bus import event_bus, Event, StateTransition, EscalationRequired
from core.state_machine import StateMachine

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    name: str = "BaseAgent"
    subscribes_to: list[type] = []

    def start(self) -> None:
        logger.info(f"Starting agent: {self.name}")
        for event_type in self.subscribes_to:
            event_bus.subscribe(event_type, self.handle)
        self.on_start()

    @abstractmethod
    def handle(self, event: Event) -> None:
        """React to an event. May emit new events. May enqueue tasks."""
        pass

    def on_start(self) -> None:
        pass

    def on_shutdown(self) -> None:
        pass

class SupervisorAgent(BaseAgent):
    """
    Top-level coordinator. Manages State Machine, Escalation Routing, and Engagement Lifecycle.
    """
    name = "SupervisorAgent"
    subscribes_to = [StateTransition, EscalationRequired]

    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine

    def on_start(self) -> None:
        logger.info("SupervisorAgent online.")
        # If starting fresh, transition to PLANNING
        if self.state_machine.current_state == "IDLE":
            self.state_machine.transition("PLANNING", "engagement.start")

    def handle(self, event: Event) -> None:
        if isinstance(event, StateTransition):
            self._handle_state_transition(event)
        elif isinstance(event, EscalationRequired):
            self._handle_escalation(event)

    def _handle_state_transition(self, event: StateTransition) -> None:
        logger.debug(f"Supervisor observed state transition: {event.from_state} -> {event.to_state}")
        # Orchestrate higher-level lifecycle logic here based on state
        pass

    def _handle_escalation(self, event: EscalationRequired) -> None:
        logger.warning(f"ESCALATION REQUIRED: Task {event.task_id} - {event.reason} (Risk: {event.risk})")
        self.state_machine.transition("ESCALATING", "escalation_event")
        # In a real implementation, notify operator via configured channel (e.g., terminal, signal)
        logger.info(f"Waiting for operator input for task {event.task_id}...")
