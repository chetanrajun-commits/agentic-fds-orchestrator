"""Command-line interface for the Agentic FDS Orchestration Engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import __version__
from .models import EngagementSpec
from .orchestrator import Orchestrator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-fds",
        description=(
            "Agentic FDS Orchestration Engine — a multi-agent SDLC pipeline "
            "for Forward Deployed Squads."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"agentic-fds {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full orchestration pipeline.")
    run.add_argument(
        "--spec",
        required=True,
        type=Path,
        help="Path to the engagement spec YAML.",
    )
    run.add_argument(
        "--workdir",
        default=Path("out"),
        type=Path,
        help="Directory for generated artifacts (default: ./out).",
    )
    run.add_argument(
        "--max-attempts",
        default=3,
        type=int,
        help="Maximum remediation attempts (default: 3).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        sys.exit(2)

    if not args.spec.exists():
        print(f"[ERROR] Spec not found: {args.spec}", file=sys.stderr)
        sys.exit(2)

    try:
        data = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
        spec = EngagementSpec(**data)
    except (TypeError, yaml.YAMLError) as exc:
        print(f"[ERROR] Invalid spec: {exc}", file=sys.stderr)
        sys.exit(2)

    orchestrator = Orchestrator(args.workdir, max_attempts=args.max_attempts)
    sys.exit(orchestrator.run(spec))


if __name__ == "__main__":
    main()
