"""Orchestrator.

The MAS loop that ties the agents together:

    Scaffold  →  Test  →  (Remediate → Re-Test)*  →  Deployment plan

The loop terminates when either:
  - the Testing Agent reports zero policy violations (success), or
  - remediation is exhausted without resolving all violations (failure).

Vector memory is scoped to the engagement namespace, mirroring the "Vector
Isolation Architecture" described in the README.
"""

from __future__ import annotations

from pathlib import Path

from .agents.deployment import DeploymentAgent
from .agents.remediation import RemediationAgent
from .agents.scaffolding import ScaffoldingAgent
from .agents.testing import TestingAgent
from .models import EngagementSpec
from .vector_memory import VectorMemory


class Orchestrator:
    def __init__(self, workdir: Path, max_attempts: int = 3) -> None:
        self.workdir = workdir
        self.max_attempts = max_attempts
        self.workdir.mkdir(parents=True, exist_ok=True)

    def run(self, spec: EngagementSpec) -> int:
        print(
            f"[ORCHESTRATOR] Engagement: client={spec.client} "
            f"squad={spec.squad} tier={spec.tier}"
        )

        memory = VectorMemory(namespace=spec.namespace)

        scaffolding = ScaffoldingAgent(self.workdir)
        s = scaffolding.run(spec)
        print(f"[SCAFFOLD]     {s.message}")

        testing = TestingAgent(self.workdir, spec)
        remediation = RemediationAgent(self.workdir, spec, memory)

        healed = False
        for attempt in range(1, self.max_attempts + 1):
            t = testing.run()
            print(f"[TEST]         {t.message}")

            if t.ok:
                healed = True
                break

            for v in t.violations:
                print(f"[TEST]           - {v.rule_id}  {v.file}: {v.message}")

            print(f"[REMEDIATE]    Attempt {attempt}/{self.max_attempts}")
            r = remediation.run(t)
            print(f"[REMEDIATE]    {r.message}")

            if not r.ok:
                print("[ORCHESTRATOR] ❌ Remediation exhausted")
                return 1

        if not healed:
            print("[ORCHESTRATOR] ❌ Policy violations remain after max attempts")
            return 1

        deployment = DeploymentAgent(self.workdir)
        d = deployment.run(spec)
        print(f"[DEPLOY]       {d.message}")

        print(f"[MEMORY]       {len(memory)} fix pattern(s) recorded (namespace={spec.namespace})")
        print("[ORCHESTRATOR] ✅ Pipeline complete")
        return 0
