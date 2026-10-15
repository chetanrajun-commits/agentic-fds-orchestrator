"""Tests for the Remediation Agent and vector memory."""

from __future__ import annotations

from pathlib import Path

import yaml

from agentic_fds.agents.remediation import RemediationAgent
from agentic_fds.agents.scaffolding import ScaffoldingAgent
from agentic_fds.agents.testing import TestingAgent
from agentic_fds.models import EngagementSpec
from agentic_fds.vector_memory import VectorMemory


def test_remediation_clears_all_violations(workdir: Path, spec: EngagementSpec) -> None:
    ScaffoldingAgent(workdir).run(spec)
    failure = TestingAgent(workdir, spec).run()
    memory = VectorMemory(namespace=spec.namespace)
    fix = RemediationAgent(workdir, spec, memory).run(failure)
    assert fix.ok
    assert TestingAgent(workdir, spec).run().ok


def test_remediation_patches_resources_and_annotations(
    workdir: Path, spec: EngagementSpec
) -> None:
    ScaffoldingAgent(workdir).run(spec)
    failure = TestingAgent(workdir, spec).run()
    memory = VectorMemory(namespace=spec.namespace)
    RemediationAgent(workdir, spec, memory).run(failure)

    dep = yaml.safe_load((workdir / "acme-corp-deployment.yaml").read_text())
    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["cpu"] == spec.cpu_limit
    assert container["resources"]["requests"]["memory"] == spec.memory_limit
    annotations = dep["spec"]["template"]["metadata"]["annotations"]
    assert annotations["sidecar.istio.io/inject"] == "true"
    assert annotations["finops.io/encryption"] == "at-rest"


def test_remediation_records_fix_in_vector_memory(
    workdir: Path, spec: EngagementSpec
) -> None:
    ScaffoldingAgent(workdir).run(spec)
    failure = TestingAgent(workdir, spec).run()
    memory = VectorMemory(namespace=spec.namespace)
    assert len(memory) == 0
    RemediationAgent(workdir, spec, memory).run(failure)
    assert len(memory) == 1
    hits = memory.query("FDS-FINOPS-001 resource limits", top_k=1)
    assert hits and hits[0].metadata["namespace"] == spec.namespace


def test_vector_memory_is_namespace_scoped() -> None:
    a = VectorMemory(namespace="tenant-a")
    b = VectorMemory(namespace="tenant-b")
    a.upsert("x", "fix for finops limits", {"namespace": "tenant-a"})
    assert len(a) == 1
    assert len(b) == 0
