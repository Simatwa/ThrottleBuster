"""Supportive functions"""

import asyncio
import logging
import re
import typing as t

from throttlebuster.constants import ILLEGAL_CHARACTERS_PATTERN

logger = logging.getLogger(__name__)
loop = asyncio.new_event_loop()


class DownloadUtils:
    @classmethod
    def bytes_to_mb(self, bytes: int) -> int:
        return round(bytes / 1_000_000, 6)

    @classmethod
    def get_offset_load(cls, content_length: int, threads: int) -> list[tuple[int, int]]:
        """Determines the bytes offset and the download size of each thread

        Args:
            content_length (int): The size of file to be downloaded in bytes.
            threads (int): Number of threads for running the download.

        Returns:
            list[tuple[int, int]]: list of byte offset and download size for each thread
        """
        assert threads > 0, f"Threads value {threads} should be at least 1"
        assert content_length > 0, f"Content-length value {content_length} should be more than 0"
        assert threads < content_length, (
            f"Threads amount {threads} should not be more than content_length {content_length}"
        )

        # Calculate base size and distribute remainder to the first few chunks
        base_size = content_length // threads
        remainder = content_length % threads
        load = [base_size + (1 if i < remainder else 0) for i in range(threads)]

        assert sum(load) == content_length, "Chunk sizes don't add up to total length"
        assert len(load) == threads, "Wrong number of chunks generated"

        # Generate (start_offset, chunk_size) pairs
        offset_load_container: list[tuple[int, int]] = []
        start = 0
        for size in load:
            offset_load_container.append((start, size))
            start += size

        return offset_load_container

    @classmethod
    def get_filename_from_header(cls, headers: dict) -> str | None:
        """Extracts filename from httpx response headers

        Args:
            headers (dict): Httpx response headers

        Returns:
            str | None: Extracted filename or None
        """
        disposition: str = headers.get("content-disposition")
        if disposition is not None:
            _, filename = disposition.split("filename=")
            return filename


def assert_instance(obj: object, class_or_tuple, name: str = "Parameter") -> t.NoReturn:
    """assert obj an instance of class_or_tuple"""

    assert isinstance(obj, class_or_tuple), (
        f"{name} value needs to be an instance of/any of {class_or_tuple} not {type(obj)}"
    )


def get_filesize_string(size_in_bytes: int) -> str:
    """Get something like `343 MB` or `1.25 GB` depending on size_in_bytes."""
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    for unit in units:
        # 1024 or 1000 ?
        if size_in_bytes >= 1000.0:
            size_in_bytes /= 1000.0
        else:
            break
    return f"{size_in_bytes:.2f} {unit}"


def get_duration_string(time_in_seconds: int) -> str:
    """Get something like `2 Mins` or `3 Secs` depending on time_in_seconds."""
    units = ["Secs", "Mins", "Hrs"]
    for unit in units:
        if time_in_seconds >= 60.0:
            time_in_seconds /= 60.0
        else:
            break
    return f"{time_in_seconds:.2f} {unit}"


def sanitize_filename(filename: str) -> str:
    """Remove illegal characters from a filename"""
    return re.sub(ILLEGAL_CHARACTERS_PATTERN, "", filename.replace(":", "-"))
