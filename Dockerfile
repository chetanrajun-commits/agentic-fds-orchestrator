FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["agentic-fds"]
CMD ["run", "--spec", "examples/engagement-spec.yaml", "--workdir", "/tmp/out"]
