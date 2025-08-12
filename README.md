<div align="center">

# ThrottleBuster

[![PyPI version](https://badge.fury.io/py/throttlebuster.svg)](https://pypi.org/project/throttlebuster)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/throttlebuster)](https://pypi.org/project/throttlebuster)
[![PyPI - License](https://img.shields.io/pypi/l/throttlebuster)](https://pypi.org/project/throttlebuster)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Hits](https://hits.sh/github.com/Simatwa/throttlebuster.svg?label=Total%20hits&logo=dotenv)](https://github.com/Simatwa/throttlebuster "Total hits")
[![Downloads](https://pepy.tech/badge/throttlebuster)](https://pepy.tech/project/throttlebuster)
<!-- 
[![Code Coverage](https://img.shields.io/codecov/c/github/Simatwa/throttlebuster)](https://codecov.io/gh/Simatwa/throttlebuster)
-->
<!-- TODO: Add logo & wakatime-->
</div>



# ThrottleBuster

This is a Python library designed to accelerate file downloads by overcoming common throttling restrictions aiming to reduce download times for large files.

Key Feature:

- Concurrent downloading across multiple threads

## Installation

```bash
$ pip install throttlebuster
```

## Usage Example

```python
from throttlebuster import ThrottleBuster

throttlebuster = ThrottleBuster()

details = throttlebuster.run_sync("http://localhost:8888/test.1.opus")

print(
    details
)

```
