"""Tests for the domain models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from agentic_fds.models import AgentResult, EngagementSpec, PolicyViolation


def test_engagement_spec_is_frozen(spec: EngagementSpec) -> None:
    with pytest.raises(FrozenInstanceError):
        spec.client = "other"  # type: ignore[misc]


def test_engagement_spec_defaults() -> None:
    s = EngagementSpec(
        client="c",
        squad="s",
        tier="dev",
        namespace="ns",
        replicas=1,
        image="img:1",
        cpu_limit="100m",
        memory_limit="128Mi",
    )
    assert s.data_classification == "internal"
    assert s.cost_center == "fds-platform"


def test_agent_result_ok_property() -> None:
    ok = AgentResult(agent="a", status="success", message="fine")
    fail = AgentResult(agent="a", status="failure", message="broken")
    assert ok.ok is True
    assert fail.ok is False


def test_policy_violation_is_structured() -> None:
    v = PolicyViolation(rule_id="FDS-FINOPS-001", file="x.yaml", message="missing limits")
    assert v.rule_id == "FDS-FINOPS-001"
    assert v.file == "x.yaml"
