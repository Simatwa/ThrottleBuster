"""Constant variables"""

import os
from pathlib import Path

CURRENT_WORKING_DIR = Path(os.getcwd())


DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
}

DEFAULT_REQUEST_COOKIES = {}

DOWNLOAD_PART_EXTENSION = ".part"

THREADS_LIMIT = 15
