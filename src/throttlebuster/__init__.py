"""
This library is designed to accelerate file downloads by overcoming
common throttling restrictions aiming to reduce download period
for large files

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

## Progress hook

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

## Synchronous

```python
from throttlebuster import ThrottleBuster

throttlebuster = ThrottleBuster()

downloaed_file = throttlebuster.run_sync("http://localhost:8888/test.1.opus")

print(
    downloaded_file
)

```
"""

from importlib import metadata

try:
    __version__ = metadata.version("throttlebuster")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Smartwa"
__repo__ = "https://github.com/Simatwa/throttlebuster"


from throttlebuster.constants import DownloadMode
from throttlebuster.core import ThrottleBuster
from throttlebuster.helpers import logger
from throttlebuster.models import DownloadedFile, DownloadTracker

__all__ = [
    "ThrottleBuster",
    "DownloadTracker",
    "DownloadedFile",
    "DownloadMode",
    "logger",
]
