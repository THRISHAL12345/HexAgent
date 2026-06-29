from dataclasses import dataclass
from datetime import datetime

@dataclass
class Observation:
    timestamp: datetime
    source: str              # tool name, event type, or "memory"
    raw_output: str          # full unprocessed output
    parsed: dict             # structured extraction (hosts, ports, vulns, etc.)
    scope_violations: list   # any out-of-scope references found in output
    token_count: int         # for context budget tracking

@dataclass
class Thought:
    observation_id: str
    interpretation: str      # what the observation means in attack context
    hypotheses: list[str]    # ranked list of possible next steps
    risks: list[str]         # risks of each hypothesis
    escalation_needed: bool  # true if any hypothesis crosses escalation threshold
    selected_hypothesis: str # the chosen next step with justification
    confidence: float        # 0.0–1.0, calibrated by the model

@dataclass
class Task:
    # Identity
    id: str                    # "recon-portscan-001"
    parent_id: str | None      # for sub-tasks
    engagement_id: str

    # What to do
    objective: str             # human-readable goal
    tool: str                  # tool plugin name (from registry)
    tool_input: dict           # inputs passed to tool.run()

    # Dependency & ordering
    dependencies: list[str]    # task IDs that must complete first
    priority: int              # 1 (highest) to 10 (lowest)

    # Constraints
    timeout_seconds: int       # executor hard-kills at this limit
    scope_check: bool          # always True unless explicitly overridden

    # Verification
    success_conditions: list[str]   # e.g. ["output.hosts.count > 0", "exit_code == 0"]
    expected_output_schema: dict    # JSON schema the output must match

    # Safety
    rollback: str | None       # shell command or function name to undo
    escalation_required: bool  # if True, pause before executing

    # Metadata
    phase: str                 # "recon" | "enum" | "vuln" | "exploit" | "post" | "report"
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    status: str                # "pending" | "running" | "done" | "failed" | "blocked"
    result: dict | None        # populated by Executor on completion

@dataclass
class VerificationResult:
    task_id: str
    success: bool
    success_conditions_met: list[str]
    conditions_failed: list[str]
    side_effects: list[str]      # unexpected but notable observations
    finding_created: bool
    next_action: str             # "continue" | "retry" | "escalate" | "abort"
