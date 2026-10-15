"""Tests for the Testing Agent policy pack."""

from __future__ import annotations

from pathlib import Path

from agentic_fds.agents.scaffolding import ScaffoldingAgent
from agentic_fds.agents.testing import TestingAgent
from agentic_fds.models import EngagementSpec


def test_testing_flags_all_four_rules(workdir: Path, spec: EngagementSpec) -> None:
    ScaffoldingAgent(workdir).run(spec)
    result = TestingAgent(workdir, spec).run()
    assert not result.ok
    rule_ids = {v.rule_id for v in result.violations}
    assert rule_ids == {
        "FDS-FINOPS-001",
        "FDS-FINOPS-002",
        "FDS-ISTIO-001",
        "FDS-SEC-001",
    }


def test_testing_skips_encryption_rule_for_internal_data(
    workdir: Path, spec: EngagementSpec
) -> None:
    internal = EngagementSpec(
        client=spec.client,
        squad=spec.squad,
        tier=spec.tier,
        namespace=spec.namespace,
        replicas=spec.replicas,
        image=spec.image,
        cpu_limit=spec.cpu_limit,
        memory_limit=spec.memory_limit,
        data_classification="internal",
        cost_center=spec.cost_center,
    )
    ScaffoldingAgent(workdir).run(internal)
    result = TestingAgent(workdir, internal).run()
    rule_ids = {v.rule_id for v in result.violations}
    assert "FDS-SEC-001" not in rule_ids


def test_testing_returns_structured_violations(
    workdir: Path, spec: EngagementSpec
) -> None:
    ScaffoldingAgent(workdir).run(spec)
    result = TestingAgent(workdir, spec).run()
    for v in result.violations:
        assert v.rule_id
        assert v.file.endswith(".yaml")
        assert v.message
