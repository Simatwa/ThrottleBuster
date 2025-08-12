# Define targets
.PHONY: install test build publish install-in-termux

# Define variables
PYTHON := python


# Default target
default: install test

# Target to install package
install:
	uv pip install -e ".[cli]"

# Target to run tests
test:
	pytest tests -v --ff

# target to build dist
build:
	rm build/ dist/ -rf
	uv build
	
# Target to publish dist to pypi
publish:
	uv publish --token $(shell get pypi)


