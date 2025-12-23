"""Constant variables"""

import os
import re
from enum import StrEnum
from pathlib import Path

CURRENT_WORKING_DIR = Path(os.getcwd())


DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/*",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) "
        "Gecko/20100101 Firefox/137.0"
    ),
}

DEFAULT_REQUEST_COOKIES = {}

DOWNLOAD_PART_EXTENSION = ".part"

DEFAULT_CHUNK_SIZE = 256
"""In kilobytes"""

DEFAULT_TASKS = 2

DEFAULT_TASKS_LIMIT = 1000

DEFAULT_READ_TIMEOUT_ATTEMPTS = 10

ILLEGAL_CHARACTERS_PATTERN = re.compile(r"[^\w\-_\.\s()&|]")


class DownloadMode(StrEnum):
    START = "start"
    RESUME = "resume"
    AUTO = "auto"

    @classmethod
    def map(cls) -> dict:
        return {"start": cls.START, "resume": cls.RESUME, "auto": cls.AUTO}
