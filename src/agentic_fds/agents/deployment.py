"""Deployment Agent.

Once all policy violations are resolved, emits a canary promotion plan:
a four-step Istio rollout with explicit promotion gates. This is the artifact
the FDS squad hands to the platform team to authorise promotion.

This agent does not apply the plan — it generates it. Application is the
platform team's job via Argo Rollouts / Flagger in production.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import AgentResult, EngagementSpec


CANARY_STEPS = [
    {"weight": 5, "duration": "5m", "gate": "error_rate < 1% and p95_latency < 500ms"},
    {"weight": 25, "duration": "10m", "gate": "error_rate < 1% and p95_latency < 500ms"},
    {"weight": 50, "duration": "15m", "gate": "error_rate < 0.5% and p95_latency < 400ms"},
    {"weight": 100, "duration": "steady", "gate": "promoted"},
]


class DeploymentAgent:
    name = "deployment"

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def run(self, spec: EngagementSpec) -> AgentResult:
        plan = {
            "engagement": {
                "client": spec.client,
                "squad": spec.squad,
                "namespace": spec.namespace,
                "tier": spec.tier,
            },
            "strategy": {
                "type": "canary",
                "mesh": "istio",
                "steps": CANARY_STEPS,
            },
            "virtualService": {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": f"{spec.client}-canary",
                    "namespace": spec.namespace,
                },
                "spec": {
                    "hosts": [f"{spec.client}-svc"],
                    "http": [
                        {
                            "route": [
                                {
                                    "destination": {
                                        "host": f"{spec.client}-svc",
                                        "subset": "canary",
                                    },
                                    "weight": 5,
                                },
                                {
                                    "destination": {
                                        "host": f"{spec.client}-svc",
                                        "subset": "stable",
                                    },
                                    "weight": 95,
                                },
                            ]
                        }
                    ],
                },
            },
            "destinationRule": {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "DestinationRule",
                "metadata": {
                    "name": f"{spec.client}-canary",
                    "namespace": spec.namespace,
                },
                "spec": {
                    "host": f"{spec.client}-svc",
                    "subsets": [
                        {"name": "stable", "labels": {"version": "stable"}},
                        {"name": "canary", "labels": {"version": "canary"}},
                    ],
                },
            },
        }

        filename = f"{spec.client}-canary-plan.yaml"
        (self.output_dir / filename).write_text(
            yaml.safe_dump(plan, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        return AgentResult(
            agent=self.name,
            status="success",
            message=(
                f"Emitted canary promotion plan for {spec.client} "
                f"({len(CANARY_STEPS)} steps, Istio mesh)"
            ),
            artifacts={"plan_file": filename},
        )
