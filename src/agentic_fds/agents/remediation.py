"""Remediation Agent.

Consumes PolicyViolations from the Testing Agent and patches the offending
manifests in place. Every successful fix is written to vector memory so that
future runs in the same namespace can retrieve it as context.

In production, this agent would call an LLM to generate a unified diff and
apply it with `git apply`. For this reference implementation, the patches are
deterministic so the pipeline runs without API keys and produces identical
output on any machine and in CI.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import yaml

from ..models import AgentResult, EngagementSpec, PolicyViolation
from ..vector_memory import VectorMemory


class RemediationAgent:
    name = "remediation"

    def __init__(
        self,
        manifests_dir: Path,
        spec: EngagementSpec,
        memory: VectorMemory,
    ) -> None:
        self.manifests_dir = manifests_dir
        self.spec = spec
        self.memory = memory

    def run(self, failure: AgentResult) -> AgentResult:
        patched_files: set[str] = set()
        applied_rules: set[str] = set()

        for violation in failure.violations:
            path = self.manifests_dir / violation.file
            if not path.exists():
                continue
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                continue
            if self._apply(doc, violation):
                path.write_text(
                    yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
                    encoding="utf-8",
                )
                patched_files.add(violation.file)
                applied_rules.add(violation.rule_id)

        if not patched_files:
            return AgentResult(
                agent=self.name,
                status="failure",
                message="No patches could be applied",
            )

        summary = (
            f"Applied {len(applied_rules)} rule(s) across {len(patched_files)} file(s): "
            + ", ".join(sorted(applied_rules))
        )
        self.memory.upsert(
            id=f"fix-{uuid.uuid4().hex[:8]}",
            text=summary,
            metadata={
                "namespace": self.spec.namespace,
                "rules": sorted(applied_rules),
            },
        )
        return AgentResult(
            agent=self.name,
            status="success",
            message=summary,
            artifacts={
                "patched_files": sorted(patched_files),
                "rules": sorted(applied_rules),
            },
        )

    def _apply(self, doc: dict, v: PolicyViolation) -> bool:
        template = doc.get("spec", {}).get("template", {})
        if not template:
            return False
        pod_meta = template.setdefault("metadata", {})
        annotations = pod_meta.setdefault("annotations", {})
        containers = template.get("spec", {}).get("containers", []) or []

        if v.rule_id in ("FDS-FINOPS-001", "FDS-FINOPS-002"):
            for container in containers:
                res = container.setdefault("resources", {})
                res.setdefault(
                    "limits",
                    {"cpu": self.spec.cpu_limit, "memory": self.spec.memory_limit},
                )
                res.setdefault(
                    "requests",
                    {"cpu": self.spec.cpu_limit, "memory": self.spec.memory_limit},
                )
            return True

        if v.rule_id == "FDS-ISTIO-001":
            annotations["sidecar.istio.io/inject"] = "true"
            return True

        if v.rule_id == "FDS-SEC-001":
            annotations["finops.io/encryption"] = "at-rest"
            return True

        return False
