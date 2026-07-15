PYTHON ?= python
PKG ?= .

.PHONY: install test discover parse-sample replay-sample book-skeleton emit-configs

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest -q

discover:
	$(PYTHON) -m group4_lab.cli discover --repo .

parse-sample:
	$(PYTHON) -m group4_lab.cli parse-file --file samples/example_module.py --output output/sample-events.jsonl

replay-sample:
	$(PYTHON) -m group4_lab.cli replay-file --before-file samples/example_module.py --after-file samples/example_module.py

book-skeleton:
	$(PYTHON) -m group4_lab.cli build-book --output docs/book

emit-configs:
	$(PYTHON) -m group4_lab.cli emit-configs --output configs/generated
