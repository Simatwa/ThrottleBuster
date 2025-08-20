# Define targets
.PHONY: install test coveragebadge

# Define variables
PYTHON := python


# Default target
default: install test

# Target to install package
install:
	uv pip install -e ".[cli]"

# Target to run tests
test:
	coverage run -m pytest -v

# Target to create coverage-badge
coveragebadge:
	coverage-badge -o assets/coverage.svg -f

# target to build dist
build:
	rm build/ dist/ -rf
	uv build
	
# Target to publish dist to pypi
publish:
	uv publish --token $(shell get pypi)


