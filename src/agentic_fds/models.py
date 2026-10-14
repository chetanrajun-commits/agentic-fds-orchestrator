"""Domain models shared across the FDS orchestration pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DataClassification = Literal["public", "internal", "confidential", "restricted"]
Tier = Literal["dev", "staging", "prod"]


@dataclass(frozen=True)
class EngagementSpec:
    """Input contract for a Forward Deployed Squad engagement.

    A squad submits one of these to the orchestrator. Everything downstream —
    scaffolding, policy validation, remediation, canary planning — reads from
    this shape.
    """

    client: str
    squad: str
    tier: Tier
    namespace: str
    replicas: int
    image: str
    cpu_limit: str
    memory_limit: str
    data_classification: DataClassification = "internal"
    cost_center: str = "fds-platform"


@dataclass(frozen=True)
class PolicyViolation:
    """A single rule failure emitted by the Testing agent."""

    rule_id: str
    file: str
    message: str


@dataclass
class AgentResult:
    """Uniform output contract for every agent in the pipeline.

    The orchestrator composes agents purely through this interface, which is
    why we can add a new agent without rewriting the pipeline.
    """

    agent: str
    status: str  # "success" | "failure"
    message: str
    artifacts: dict[str, Any] = field(default_factory=dict)
    violations: list[PolicyViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "success"
