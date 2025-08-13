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
- Ready to use commandline tool


## Installation

```bash
$ pip install "throttlebuster[cli]"
```

## Usage

For testing purposes you can use this config example for [Nginx](htts://nginx.org) server.

```conf
# Test server

# Nginx config file
# Copy it to /etc/sites-enabled or add it to default nginx.conf file

server {
    listen 8888;
    server_name throttlebuster.test;

    location / {
        limit_rate 500k;  # Limit rate to 500 KB/s
        root /home/smartwa/y2mate;  # Set your own directory
        index index.html;
    }
}

```

<details open>

<summary>

### Developer
</summary>

```python

from throttlebuster import ThrottleBuster

async def main():
    throttlebuster = ThrottleBuster(threads=4)
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

#### Custom progress hook

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

<details>

<summary>

```sh
$ python -m throttlebuster --help
```
</summary>

```sh
Usage: python -m throttlebuster [OPTIONS] COMMAND [ARGS]...

  Accelerate file downloads by overcoming common throttling restrictions
  envvar-prefix : THROTTLEBUSTER.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  download  Download file using http protocol
  estimate  Estimate download duration for different threads

```

</details>

#### Download

```sh
$ python -m throttlebuster download http://localhost:8888/test.1.opus --threads 14
```

<details>

<summary>

```sh
$ python -m throttlebuster download --help
```
</summary>

```sh
Usage: python -m throttlebuster download [OPTIONS] URL

  Download file using http protocol

Options:
  -T, --threads INTEGER RANGE     Number of threads to carry out the download
                                  : 2  [1<=x<=1000]
  -C, --chunk-size INTEGER        Streaming download chunk size in kilobytes :
                                  256
  -D, --dir DIRECTORY             Directory for saving the downloaded file to
                                  : PWD
  -P, --part-dir DIRECTORY        Directory for temporarily saving the
                                  downloaded file-parts to : PWD
  -E, --part-extension TEXT       Filename extension for download parts :
                                  .part
  -H, --request-headers TEXT...   Httpx request headers : default
  -B, --merge-buffer-size INTEGER RANGE
                                  Buffer size for merging the separated files
                                  in kilobytes : 256  [1<=x<=102400]
  -F, --filename TEXT             Filename for the downloaded content
  -M, --download-mode [start|resume|auto]
                                  Whether to start or resume incomplete
                                  download : auto
  -L, --file_size INTEGER         Size of the file to be downloaded : None
  -K, --colour TEXT               Progress bar display color : cyan
  -k, --keep-parts                Whether to retain the separate download
                                  parts : False
  -s, --simple                    Show percentage and bar only in progressbar
                                  : False
  -t, --test                      Just test if download is possible but do not
                                  actually download : False
  -a, --ascii                     Use unicode (smooth blocks) to fill the
                                  progress-bar meter : False
  -l, --no-leave                  Do not keep all leaves of the progressbar :
                                  False
  -z, --disable-progress-bar      Do not show progress_bar : False
  -q, --quiet                     Do not show any interactive information :
                                  False
  -v, --verbose                   Show more detailed information : 0
  --help                          Show this message and exit.
```

</details>

> [!TIP]
> Shortcuts for `$ python -m throttlebuster` are `$ throttlebuster` & `$ tbust`

#### Estimate

<details>

<summary>

```sh
$ python -m throttlebuster estimate --url http://localhost:8888/miel-martin.webm 260000

```
</summary>

```sh
         337.88 MB at 260.00 KB/s         
┏━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Threads ┃ Duration   ┃ Load per thread ┃
┡━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 20      │ 1.08 Mins  │ 16.89 MB        │
│ 19      │ 1.14 Mins  │ 17.78 MB        │
│ 18      │ 1.20 Mins  │ 18.77 MB        │
│ 17      │ 1.27 Mins  │ 19.88 MB        │
│ 16      │ 1.35 Mins  │ 21.12 MB        │
│ 15      │ 1.44 Mins  │ 22.53 MB        │
│ 14      │ 1.55 Mins  │ 24.13 MB        │
│ 13      │ 1.67 Mins  │ 25.99 MB        │
│ 12      │ 1.80 Mins  │ 28.16 MB        │
│ 11      │ 1.97 Mins  │ 30.72 MB        │
│ 10      │ 2.17 Mins  │ 33.79 MB        │
│ 9       │ 2.41 Mins  │ 37.54 MB        │
│ 8       │ 2.71 Mins  │ 42.24 MB        │
│ 7       │ 3.09 Mins  │ 48.27 MB        │
│ 6       │ 3.61 Mins  │ 56.31 MB        │
│ 5       │ 4.33 Mins  │ 67.58 MB        │
│ 4       │ 5.41 Mins  │ 84.47 MB        │
│ 3       │ 7.22 Mins  │ 112.63 MB       │
│ 2       │ 10.83 Mins │ 168.94 MB       │
└─────────┴────────────┴─────────────────┘
```

</details>


<details>

<summary>

```sh
$ python -m throttlebuster estimate --help
```
</summary>

```sh
Usage: python -m throttlebuster estimate [OPTIONS] THROTTLE

  Estimate download duration for different threads

Options:
  -U, --url TEXT               Url to the target file
  -S, --size INTEGER           Size in bytes of the targeted file
  -T, --threads INTEGER RANGE  Threads amount to base the estimate on : Range
                               (2-30)  [1<=x<=1000]
  -j, --json                   Stdout estimates in json format
  --help                       Show this message and exit.
```

</details>

Throttle unit is **bytes**.

## [Motive](#features)

<div align="center">

[Back to Top](#throttlebuster)

</div>
