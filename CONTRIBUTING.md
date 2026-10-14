# Contributing

Thanks for your interest. This is a reference implementation, and contributions
are welcome — especially around additional agents (cost, security, compliance).

## Local development

```bash
git clone https://github.com/chetanrajun-commits/agentic-fds-orchestrator.git
cd agentic-fds-orchestrator
make dev
make test
make run
```

## Adding a new agent

1. Create `src/agentic_fds/agents/<name>.py`.
2. Implement a `run(self, ...) -> AgentResult` method.
3. Wire it into `Orchestrator` in `src/agentic_fds/orchestrator.py`.
4. Add a test under `tests/`.
5. Update `docs/architecture.md`.

## Code style

- `ruff check src tests` must pass.
- Line length 100.
- Type hints on public functions.

## Commit messages

Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
