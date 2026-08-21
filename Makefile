SHELL := /usr/bin/env bash
PYTHON ?= python3

.PHONY: test typecheck validate verify preview screenshots package

test:
	pytest -q

typecheck:
	bash scripts/build-frontends.sh --check

validate:
	$(PYTHON) scripts/validate_repository.py
	find scripts -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n

verify: test typecheck validate
	@echo "SmartDiag504 verification passed"

preview:
	docker compose -f compose.preview.yaml up --build

screenshots:
	bash scripts/capture-previews.sh

package:
	bash scripts/package-release.sh
