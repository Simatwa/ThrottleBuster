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

This is a Python library designed to accelerate file downloads by overcoming common throttling restrictions aiming to reduce download duration for large files.

## Features

- Concurrent downloading across multiple threads
- Fully asynchronous with synchronous support


## Installation

```bash
$ pip install throttlebuster
```

## Usage

<details open>

<summary>

### Developer
</summary>

```python

from throttlebuster import ThrottleBuster

async def main():
    throttlebuster = ThrottleBuster()
    downloaded_file = await throttlebuster.run(
        "http://localhost:8888/test.1.opus",
    )
    print(
        downloaded_file
    )

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

```

Perform download with custom progress hook

```python
from throttlebuster import DownloadTracker, ThrottleBuster


async def callback_function(data: DownloadTracker):
    percent = (data.downloaded_size / data.expected_size) * 100
    print(f"> Downloading {data.saved_to.name} {percent:.2f}%", end="\r")


async def main():
    throttlebuster = ThrottleBuster(threads=1)
    downloaded_file await throttlebuster.run(
        "http://localhost:8888/test.1.opus", progress_hook=callback_function
    )
    print(
        downloaded_file
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

```

<details>

<summary>

#### Synchronous
</summary>

```python
from throttlebuster import ThrottleBuster

throttlebuster = ThrottleBuster()

downloaed_file = throttlebuster.run_sync("http://localhost:8888/test.1.opus")

print(
    downloaded_file
)

```
</details>

</details>

### Commandline

```
$ echo "Coming soon!"
```
