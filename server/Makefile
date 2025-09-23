.PHONY: run example1 mypy test

all: run

run:
	uv run hippopytamus/main.py

example1:
	uv run hippopytamus/example/main.py

mypy:
	uvx mypy hippopytamus/

test:
	uvx pytest
