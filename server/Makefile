.PHONY: run example1 example2 example3 example4 example5 mypy test

all: run

run:
	uv run hippopytamus/main.py

example1:
	uv run hippopytamus/example/example1/main.py

example2:
	uv run hippopytamus/example/example2/main.py

example3:
	uv run hippopytamus/example/example3/main.py

example4:
	uv run hippopytamus/example/example4/main.py

example5:
	uv run hippopytamus/example/example5/main.py

mypy:
	uvx mypy hippopytamus/

test:
	uvx pytest
