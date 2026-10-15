"""Shared fixtures for the FDS pipeline test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_fds.models import EngagementSpec


@pytest.fixture
def spec() -> EngagementSpec:
    """A minimal engagement spec exercising every policy rule."""
    return EngagementSpec(
        client="acme-corp",
        squad="atlas",
        tier="prod",
        namespace="fds-acme-prod",
        replicas=3,
        image="ghcr.io/acme/portfolio-api:1.4.2",
        cpu_limit="500m",
        memory_limit="512Mi",
        data_classification="confidential",
        cost_center="fds-atlas",
    )


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    """Isolated output directory per test."""
    d = tmp_path / "out"
    d.mkdir()
    return d
