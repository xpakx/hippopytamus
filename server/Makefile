.PHONY: run example1 mypy test

all: run

run:
	uv run hippopytamus/main.py

example1:
	uv run hippopytamus/example/example1/main.py

example2:
	uv run hippopytamus/example/example2/main.py

mypy:
	uvx mypy hippopytamus/

test:
	uvx pytest
