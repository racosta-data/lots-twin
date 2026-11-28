.PHONY: install test simulate

install:
	pip install -e ".[dev]"

test:
	pytest -q

simulate:
	python -m lots_twin.pipeline.cli simulate
