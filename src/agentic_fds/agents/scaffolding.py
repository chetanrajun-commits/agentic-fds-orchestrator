"""Scaffolding Agent.

Interprets an EngagementSpec and renders the base Kubernetes manifests for a
Forward Deployed Squad engagement: Namespace, Deployment, Service.

Note: the Deployment is rendered *without* resource limits and *without* the
Istio sidecar annotation. This is intentional — the Testing Agent will flag
both, and the Remediation Agent will patch them. That is the self-healing loop
this repository demonstrates.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import AgentResult, EngagementSpec


class ScaffoldingAgent:
    name = "scaffolding"

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def run(self, spec: EngagementSpec) -> AgentResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        manifests = self._render(spec)
        for filename, doc in manifests.items():
            (self.output_dir / filename).write_text(
                yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
                encoding="utf-8",
            )
        return AgentResult(
            agent=self.name,
            status="success",
            message=f"Generated {len(manifests)} manifest(s) for engagement {spec.client}",
            artifacts={"manifests": list(manifests.keys())},
        )

    def _render(self, spec: EngagementSpec) -> dict[str, dict]:
        return {
            f"{spec.client}-namespace.yaml": self._namespace(spec),
            f"{spec.client}-deployment.yaml": self._deployment(spec),
            f"{spec.client}-service.yaml": self._service(spec),
        }

    def _labels(self, spec: EngagementSpec) -> dict:
        return {
            "app": spec.client,
            "client": spec.client,
            "squad": spec.squad,
            "cost-center": spec.cost_center,
        }

    def _namespace(self, spec: EngagementSpec) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": spec.namespace,
                "labels": self._labels(spec),
            },
        }

    def _deployment(self, spec: EngagementSpec) -> dict:
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{spec.client}-app",
                "namespace": spec.namespace,
                "labels": self._labels(spec),
            },
            "spec": {
                "replicas": spec.replicas,
                "selector": {"matchLabels": {"app": spec.client}},
                "template": {
                    "metadata": {
                        "labels": {"app": spec.client},
                        "annotations": {},
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": spec.client,
                                "image": spec.image,
                                "ports": [{"containerPort": 8080}],
                            }
                        ]
                    },
                },
            },
        }

    def _service(self, spec: EngagementSpec) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{spec.client}-svc",
                "namespace": spec.namespace,
                "labels": self._labels(spec),
            },
            "spec": {
                "selector": {"app": spec.client},
                "ports": [{"port": 80, "targetPort": 8080, "name": "http"}],
            },
        }
