"""End-to-end test of the multi-agent orchestration loop."""

from __future__ import annotations

from pathlib import Path

from agentic_fds.agents.testing import TestingAgent
from agentic_fds.models import EngagementSpec
from agentic_fds.orchestrator import Orchestrator


def test_full_pipeline_self_heals_and_emits_canary_plan(
    workdir: Path, spec: EngagementSpec
) -> None:
    exit_code = Orchestrator(workdir, max_attempts=3).run(spec)

    assert exit_code == 0
    assert TestingAgent(workdir, spec).run().ok

    plan = workdir / "acme-corp-canary-plan.yaml"
    assert plan.exists()


def test_pipeline_fails_when_remediation_cannot_fix(
    workdir: Path, spec: EngagementSpec, monkeypatch
) -> None:
    """If the remediation agent is a no-op, the pipeline must exit non-zero."""

    from agentic_fds.agents import remediation as rem_mod

    def noop(self, failure):  # type: ignore[no-untyped-def]
        from agentic_fds.models import AgentResult

        return AgentResult(agent=self.name, status="failure", message="no-op")

    monkeypatch.setattr(rem_mod.RemediationAgent, "run", noop)

    exit_code = Orchestrator(workdir, max_attempts=2).run(spec)
    assert exit_code == 1
