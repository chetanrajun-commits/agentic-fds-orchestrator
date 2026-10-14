"""Testing Agent.

Validates generated manifests against the FDS policy pack:

    FDS-FINOPS-001  Deployment container missing resource limits
    FDS-FINOPS-002  Deployment container missing resource requests
    FDS-ISTIO-001   Pod template missing Istio sidecar injection annotation
    FDS-SEC-001     Confidential/restricted data without at-rest encryption annotation

Every violation is returned as a structured PolicyViolation. The Remediation
Agent consumes these directly — no parsing of free-text logs.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import AgentResult, EngagementSpec, PolicyViolation


POLICY_PACK = "fds-policy-pack-v1"


class TestingAgent:
    name = "testing"

    def __init__(self, manifests_dir: Path, spec: EngagementSpec) -> None:
        self.manifests_dir = manifests_dir
        self.spec = spec

    def run(self) -> AgentResult:
        violations: list[PolicyViolation] = []
        for path in sorted(self.manifests_dir.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and doc.get("kind") == "Deployment":
                violations.extend(self._check_deployment(path.name, doc))

        if violations:
            return AgentResult(
                agent=self.name,
                status="failure",
                message=f"{len(violations)} policy violation(s) under {POLICY_PACK}",
                violations=violations,
            )
        return AgentResult(
            agent=self.name,
            status="success",
            message=f"All manifests passed {POLICY_PACK}",
        )

    def _check_deployment(self, filename: str, doc: dict) -> list[PolicyViolation]:
        out: list[PolicyViolation] = []
        template = doc.get("spec", {}).get("template", {})
        pod_meta = template.get("metadata", {}) or {}
        annotations = pod_meta.get("annotations", {}) or {}
        containers = template.get("spec", {}).get("containers", []) or []

        for container in containers:
            res = container.get("resources") or {}
            if "limits" not in res:
                out.append(
                    PolicyViolation(
                        rule_id="FDS-FINOPS-001",
                        file=filename,
                        message=f"container '{container.get('name')}' missing resource limits",
                    )
                )
            if "requests" not in res:
                out.append(
                    PolicyViolation(
                        rule_id="FDS-FINOPS-002",
                        file=filename,
                        message=f"container '{container.get('name')}' missing resource requests",
                    )
                )

        if annotations.get("sidecar.istio.io/inject") != "true":
            out.append(
                PolicyViolation(
                    rule_id="FDS-ISTIO-001",
                    file=filename,
                    message="pod template missing Istio sidecar injection annotation",
                )
            )

        if self.spec.data_classification in ("confidential", "restricted"):
            if annotations.get("finops.io/encryption") != "at-rest":
                out.append(
                    PolicyViolation(
                        rule_id="FDS-SEC-001",
                        file=filename,
                        message=(
                            f"data_classification={self.spec.data_classification} requires "
                            "finops.io/encryption: at-rest annotation"
                        ),
                    )
                )

        return out
