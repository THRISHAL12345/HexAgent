import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Type, Dict, List

logger = logging.getLogger(__name__)

class Event:
    pass

class EventBus:
    def __init__(self, log_file: str = "logs/events.jsonl"):
        self._subscribers: Dict[Type[Event], List[Callable]] = {}
        self.log_file = log_file

    def emit(self, event: Event) -> None:
        event_type = type(event)
        
        # Persist event
        self._log_event(event)
        
        # Notify subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__} for event {event_type.__name__}: {e}")

    def subscribe(self, event_type: Type[Event], handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def _log_event(self, event: Event) -> None:
        try:
            with open(self.log_file, "a") as f:
                data = asdict(event)  # type: ignore
                data["_type"] = type(event).__name__
                # Convert datetimes to strings
                for k, v in data.items():
                    if isinstance(v, datetime):
                        data[k] = v.isoformat()
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def replay(self, since: datetime) -> list[Event]:
        # TODO: Implement crash recovery replay logic
        return []

# Recon events
@dataclass
class PortFound(Event):
    host: str
    port: int
    protocol: str
    timestamp: datetime

@dataclass
class ServiceDetected(Event):
    host: str
    port: int
    service: str
    version: str
    banner: str

@dataclass
class SubdomainFound(Event):
    domain: str
    ip: str | None
    source: str

# Enumeration events
@dataclass
class EnumerationRequested(Event):
    host: str
    service: str
    reason: str

@dataclass
class CredentialFound(Event):
    host: str
    service: str
    username: str
    password_hash: str
    source: str

# Vulnerability events
@dataclass
class VulnerabilityHypothesised(Event):
    host: str
    title: str
    severity: str
    confidence: float
    evidence: str

@dataclass
class FindingCreated(Event):
    finding_id: str
    host: str
    title: str
    severity: str
    confirmed: bool

@dataclass
class FindingConfirmed(Event):
    finding_id: str
    poc_path: str
    cvss_score: float

# State events
@dataclass
class TaskCompleted(Event):
    task_id: str
    raw_output: str
    duration_seconds: float

@dataclass
class TaskFailed(Event):
    task_id: str
    error: str
    rollback_executed: bool

@dataclass
class EscalationRequired(Event):
    task_id: str
    reason: str
    risk: str
    awaiting_operator: bool

@dataclass
class StateTransition(Event):
    from_state: str
    to_state: str
    trigger: str

# Memory events
@dataclass
class MemoryUpdated(Event):
    entity_type: str
    entity_id: str
    change: str

@dataclass
class ReportUpdated(Event):
    section: str
    finding_count: int
    severity_counts: dict

# Singleton instance
event_bus = EventBus()
