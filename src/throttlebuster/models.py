"""Dataclasses module"""

from dataclasses import dataclass, field
from pathlib import Path

from throttlebuster.constants import DownloadMode


@dataclass(frozen=False)
class DownloadTracker:
    """Download part metadata"""

    url: str
    saved_to: Path
    index: int
    bytes_offset: int
    expected_size: int
    streaming_chunk_size: int = 0
    downloaded_size: int = 0
    download_mode: DownloadMode = DownloadMode.AUTO

    @property
    def is_complete(self) -> bool:
        """Checks whether the download was complete"""
        return self.downloaded_size >= self.expected_size

    def update_downloaded_size(self, new_chunk_size: int) -> int:
        """Updates the downloaded size value

        Args:
            new_chunk_size (int): Streaming chunk size

        Returns:
            int: New downloaded-size value
        """
        self.streaming_chunk_size = new_chunk_size
        self.downloaded_size += new_chunk_size
        return self.downloaded_size


@dataclass(frozen=True)
class DownloadedFile:
    """Completed download file metadata"""

    url: str
    saved_to: Path
    expected_size: int
    size: int
    duration: int
    """Download time in seconds"""
    merge_duration: int
    file_parts: list[DownloadTracker] = field(default_factory=list)

    @property
    def threads_used(self) -> int:
        return len(self.file_parts)

    @property
    def is_complete(self) -> bool:
        return self.expected_size == self.size
