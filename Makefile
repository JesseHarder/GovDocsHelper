PROJECT_NAME = gov_docs_helper

black:  ## Format code with black.
	black -l 88 .

black-check:  ## Format code with black.
	black -l 88 --check .

check: mypy flake8 docstyle black-check isort-check

docstyle:
	pydocstyle $(PROJECT_NAME)/
	#pydocstyle tests/

flake8:  ## Flake8 check of codebase.
	flake8 --max-line-length=88 $(PROJECT_NAME)/
#	flake8 --max-line-length=88 tests/

format: isort black  ## Format with isort and black.

isort:  ## Format imports with isort
	isort --profile black .
#	isort --profile black tests/

isort-check:  ## Format imports with isort
	isort --profile black --check --diff $(PROJECT_NAME)/
#	isort --profile black --check --diff tests/

mypy:  ## Mypy check of codebase.
	mypy --show-error-codes --ignore-missing-imports $(PROJECT_NAME)/
#	mypy --show-error-codes --ignore-missing-imports tests/
