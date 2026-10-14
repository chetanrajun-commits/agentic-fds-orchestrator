.PHONY: install dev test lint run demo clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

run:
	python -m agentic_fds run --spec examples/engagement-spec.yaml --workdir out

demo: install
	python -m agentic_fds run --spec examples/engagement-spec.yaml --workdir out

clean:
	rm -rf out .pytest_cache .ruff_cache **/__pycache__
