"""Tests for the Scaffolding Agent."""

from __future__ import annotations

from pathlib import Path

import yaml

from agentic_fds.agents.scaffolding import ScaffoldingAgent
from agentic_fds.models import EngagementSpec


def test_scaffolding_writes_three_manifests(workdir: Path, spec: EngagementSpec) -> None:
    result = ScaffoldingAgent(workdir).run(spec)
    assert result.ok
    files = sorted(p.name for p in workdir.glob("*.yaml"))
    assert files == [
        "acme-corp-deployment.yaml",
        "acme-corp-namespace.yaml",
        "acme-corp-service.yaml",
    ]


def test_scaffolding_applies_finops_labels(workdir: Path, spec: EngagementSpec) -> None:
    ScaffoldingAgent(workdir).run(spec)
    ns = yaml.safe_load((workdir / "acme-corp-namespace.yaml").read_text())
    labels = ns["metadata"]["labels"]
    assert labels["client"] == "acme-corp"
    assert labels["squad"] == "atlas"
    assert labels["cost-center"] == "fds-atlas"


def test_scaffolding_intentionally_omits_resources(
    workdir: Path, spec: EngagementSpec
) -> None:
    """The Deployment must NOT have resource limits or Istio annotations.

    This is by design — the Testing Agent flags them and the Remediation Agent
    patches them. If this test ever fails, the self-healing loop is broken.
    """
    ScaffoldingAgent(workdir).run(spec)
    dep = yaml.safe_load((workdir / "acme-corp-deployment.yaml").read_text())
    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert "resources" not in container
    annotations = dep["spec"]["template"]["metadata"].get("annotations", {})
    assert "sidecar.istio.io/inject" not in annotations
