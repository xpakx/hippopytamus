.PHONY: run mypy test $(EXAMPLES)
EXAMPLES := $(notdir $(wildcard hippopytamus/example/*))

all: run

run:
	uv run hippopytamus/main.py

$(EXAMPLES):
	uv run hippopytamus/example/$@/main.py

mypy:
	uvx mypy hippopytamus/

test:
	uvx pytest
