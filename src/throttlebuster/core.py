"""Main module"""

import asyncio
import os
import warnings
from pathlib import Path

import httpx
import tqdm
from httpx._types import HeaderTypes

from throttlebuster.constants import (
    CURRENT_WORKING_DIR,
    DEFAULT_REQUEST_HEADERS,
    DOWNLOAD_PART_EXTENSION,
    THREADS_LIMIT,
)
from throttlebuster.exceptions import FilenameNotFoundError, FilesizeNotFoundError
from throttlebuster.helpers import (
    DownloadUtils,
    get_filesize_string,
)
from throttlebuster.models import DownloadTracker

warnings.simplefilter("ignore", category=(tqdm.std.TqdmWarning,))
"""Raised due to frac*"""


class ThrottleBuster(DownloadUtils):
    """Performs file download using multiple threads in attempt
    to bypass the throttling limit. The download time `(t)` reduces
    to a new value `(nt)` by value `nt = t / th` where `(th)` is the
    threads amount.

    This will only be useful when the throttling is done per `download
    stream` and NOT `per IP address`.
    """

    threads_limit: int = THREADS_LIMIT
    """Number of threads not to exceed"""

    def __init__(
        self,
        dir: Path | str = CURRENT_WORKING_DIR,
        chunk_size: int = 64,
        threads: int = 2,
        part_dir: Path | str = CURRENT_WORKING_DIR,
        part_extension: str = DOWNLOAD_PART_EXTENSION,
        request_headers: HeaderTypes = DEFAULT_REQUEST_HEADERS,
        **kwargs,
    ):
        """Constructor for `ThrottleBuster`

        Args:
            dir (Path | str, optional): Directory for saving the downloaded file. Defaults to CURRENT_WORKING_DIR.
            chunk_size (int, optional): Streaming download chunk size in kilobytes. Defaults to 64.
            threads (int, optional): Number of threads to carry out the download. Defaults to 2.
            part_extension (str, optional): Filename extension for download parts. Defaults to DOWNLOAD_PART_EXTENSION.
            request_headers (HeaderTypes, optional): Request headers. Defaults to DEFAULT_REQUEST_HEADERS.

        kwargs : Keyword arguments for `httpx.AsyncClient`
        """  # noqa: E501
        # TODO: add temp-dir
        assert threads > 0 and threads < self.threads_limit, (
            f"Value for threads should be atleast 1 and at most {self.threads_limit}"
        )

        self.chunk_size = chunk_size * 1_024
        self.threads = int(threads)
        self.dir = Path(dir)
        self.part_dir = Path(part_dir)
        self.part_extension = part_extension
        self.client = httpx.AsyncClient(**kwargs)
        """httpx AsyncClient"""
        self.client.headers.update(request_headers)

    def __repr__(self) -> str:
        return (
            rf"{self.__module__}.{self.__class__.__name__} "
            rf'dir="{self.dir}", chunk_size_in_bytes={self.chunk_size}>'
        )

    def generate_saved_to(self, filename: str, index: int = 0) -> Path:
        filename, ext = os.path.splitext(filename)
        index = f".{index}" if index is not None else ""
        ext = "." + ext if ext else ""

        return self.dir.joinpath(f"{filename}{index}{ext}")

    def _create_headers(self, bytes_offset: int) -> dict:
        new_headers = self.client.headers.copy()
        new_headers["Range"] = f"bytes={bytes_offset}-"
        return new_headers

    async def _call_progress_hook(self, progress_hook: callable, download_tracker: DownloadTracker) -> None:
        """Interacts with progress book"""
        if progress_hook is None:
            return

        if asyncio.iscoroutinefunction(progress_hook):
            await progress_hook(download_tracker)

        else:
            progress_hook(download_tracker)
            # NOTE: Consider using status code to determine whether to proceed
            # with download process or not

    def _merge_parts(
        self,
        file_parts: list[DownloadTracker],
        filename: Path,
        clear_parts: bool = True,
    ) -> Path:
        """Combines the separated download parts into one.

        Args:
            file_parts (list[DownloadTracker]): List of the separate tracks
            filename (Path): Filename for saving the merged parts under.
            clear_parts (bool, optional): Whether to delete the download parts. Defaults to True.

        Returns:
            Path: Filepath to the merged parts.
        """
        ordered_parts: list[DownloadTracker] = []
        for part in file_parts:
            assert part.saved_to.exists(), f"Part not found in downloaded path {part}"
            assert part.is_complete, f"Incomplete file part {part}"
            ordered_parts.insert(part.index, part)

        with open(
            filename,
            "wb+",
        ) as fh:
            for part in ordered_parts:
                with open(part.saved_to, "rb") as part_fh:
                    fh.write(part_fh.read(part.expected_size))

                if clear_parts:
                    os.remove(part.saved_to)

        return filename

    async def _downloader(
        self,
        download_tracker: DownloadTracker,
        progress_bar: tqdm.tqdm,
        progress_hook: callable,
    ) -> DownloadTracker:
        """Downloads each download part"""
        async with self.client.stream(
            "GET",
            url=download_tracker.url,
            headers=self._create_headers(download_tracker.bytes_offset),
        ) as stream:
            stream.raise_for_status()
            with open(download_tracker.saved_to, "wb") as fh:
                async for chunk in stream.aiter_bytes(self.chunk_size):
                    fh.write(chunk)
                    download_tracker.update_downloaded_size(len(chunk))
                    progress_bar.update(self.bytes_to_mb(download_tracker.streaming_chunk_size))
                    await self._call_progress_hook(progress_hook, download_tracker)
                    if download_tracker.is_complete:
                        # Done downloading it's part
                        break

        return download_tracker

    async def run(
        self,
        url: str,
        filename: str = None,
        progress_hook: callable = None,
        disable_progress_bar: bool = None,
        file_size: int = None,
        colour: str = "cyan",
        simple: bool = False,
        test: bool = False,
        leave: bool = True,
        ascii: bool = False,
        **kwargs,
    ) -> Path | httpx.Response:
        """Controls the whole download process of a file.

        Args:
            url (str): Url of the file to be downloaded.
            filename (str, optional): Filename for the downloaded content. Defaults to None.
            progress_hook (callable, optional): Function to call with the download progress information. Defaults to None.
            disable_progress_bar (bool, optional): Do not show progress_bar. Defaults to None (decide based on progress_hook).
            file_size (int, optional): Size of the file to be downloaded. Defaults to None.
            leave (bool, optional): Keep all leaves of the progressbar. Defaults to True.
            colour (str, optional): Progress bar display color. Defaults to "cyan".
            simple (bool, optional): Show percentage and bar only in progressbar. Deafults to False.
            test (bool, optional): Just test if download is possible but do not actually download. Defaults to False.
            ascii (bool, optional): Use unicode (smooth blocks) to fill the progress-bar meter. Defaults to False.

        kwargs: Other keyword arguments for `tqdm.tdqm`

        Returns:
            Path | httpx.Response: Path where the media file has been saved to or httpx Response (test).
        """  # noqa: E501

        async_task_items = []
        download_tracker_items = []

        if disable_progress_bar is None:
            disable_progress_bar = progress_hook is not None

        async with self.client.stream("GET", url=url) as stream:
            stream.raise_for_status()

            if test:
                return stream

            content_length = stream.headers.get("content-length", file_size)
            if type(content_length) is str:
                content_length = int(content_length)

            filename = filename or self.get_filename_from_header(stream.headers)

            if filename is None:
                raise FilenameNotFoundError(
                    "Unable to get filename. Pass filename value to suppress this error"
                )

            if content_length is None:
                raise FilesizeNotFoundError(
                    "Unable to get the content-length of the file from server response. "
                    "Set the content-length using parameter file_size to suppress this error."
                )

            size_with_unit = get_filesize_string(content_length)
            filename_disp = filename if len(filename) < 8 else filename[:8] + "..."

            p_bar = tqdm.tqdm(
                total=self.bytes_to_mb(content_length),
                desc=f"Downloading{' ' if simple else f' [{filename_disp}]'}",
                unit="Mb",
                disable=disable_progress_bar,
                colour=colour,
                leave=leave,
                ascii=ascii,
                bar_format=(
                    "{l_bar}{bar} | %(size)s" % (dict(size=size_with_unit))
                    if simple
                    else "{l_bar}{bar}{r_bar}"
                ),
                **kwargs,
            )

            for index, offset_load in enumerate(self.get_offset_load(content_length, self.threads)):
                offset, load = offset_load
                download_tracker = DownloadTracker(
                    url=url,
                    saved_to=self.generate_saved_to(filename + self.part_extension, index),
                    index=index,
                    bytes_offset=offset,
                    expected_size=load,
                )

                download_tracker_items.append(download_tracker)
                async_task = asyncio.create_task(
                    self._downloader(
                        download_tracker,
                        progress_bar=p_bar,
                        progress_hook=progress_hook,
                    )
                )
                async_task_items.append(async_task)

            file_parts = await asyncio.gather(*async_task_items)
            return self._merge_parts(file_parts, filename=filename)
