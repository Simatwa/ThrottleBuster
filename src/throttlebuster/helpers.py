"""Supportive functions"""

import asyncio
import logging

logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()


class DownloadUtils:
    @classmethod
    def bytes_to_mb(self, bytes: int) -> int:
        return abs(bytes / 1_000_000)

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
