"""Main module"""

import asyncio
import os
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import httpx
from httpx._types import HeaderTypes

from throttlebuster.constants import (
    CURRENT_WORKING_DIR,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_REQUEST_HEADERS,
    DEFAULT_TASKS,
    DEFAULT_TASKS_LIMIT,
    DEFAULT_READ_TIMEOUT_ATTEMPTS,
    DOWNLOAD_PART_EXTENSION,
    DownloadMode,
)
from throttlebuster.exceptions import (
    FilenameNotFoundError,
    FilesizeNotFoundError,
    IncompatibleServerError,
)
from throttlebuster.helpers import (
    CustomTqdm,
    DownloadUtils,
    assert_instance,
    get_duration_string,
    get_filesize_string,
    logger,
    sanitize_filename,
)
from throttlebuster.models import DownloadedFile, DownloadTracker


class ThrottleBuster(DownloadUtils):
    """Performs file download using multiple tasks in attempt
    to bypass the throttling limit. The download time `(t)` reduces
    to a new value `(nt)` by value `nt = t / th` where `(th)` is the
    tasks amount.

    This will only be useful when the throttling is done per `download
    stream` and NOT `per IP address` and server supports resuming download.

    #### NOTE
    Remember that increasing the number of concurrent tasks beyond what your
    system can handle efficiently may lead to performance degradation rather
    than improvement
    """

    tasks_limit: int = DEFAULT_TASKS_LIMIT
    """Number of tasks not to exceed"""

    def __init__(
        self,
        dir: Path | str = CURRENT_WORKING_DIR,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        tasks: int = DEFAULT_TASKS,
        part_dir: Path | str = CURRENT_WORKING_DIR,
        part_extension: str = DOWNLOAD_PART_EXTENSION,
        request_headers: HeaderTypes = DEFAULT_REQUEST_HEADERS,
        merge_buffer_size: int | None = None,
        **kwargs,
    ):
        """Constructor for `ThrottleBuster`

        Args:
            dir (Path | str, optional): Directory for saving downloaded files to. Defaults to CURRENT_WORKING_DIR.
            chunk_size (int, optional): Streaming download chunk size in kilobytes. Defaults to DEFAULT_CHUNK_SIZE.
            tasks (int, optional): Number of async tasks to carry out the download. Defaults to DEFAULT_TASKS.
            part_dir (Path | str, optional): Directory for temporarily saving downloaded file-parts to. Defaults to CURRENT_WORKING_DIR.
            part_extension (str, optional): Filename extension for download parts. Defaults to DOWNLOAD_PART_EXTENSION.
            request_headers (HeaderTypes, optional): Httpx request headers. Defaults to DEFAULT_REQUEST_HEADERS.
            merge_buffer_size (int|None, optional). Buffer size for merging the separated files in kilobytes. Defaults to chunk_size.

        kwargs : Keyword arguments for `httpx.AsyncClient`
        """  # noqa: E501
        # TODO: add temp-dir
        assert tasks > 0 and tasks <= self.tasks_limit, (
            f"Value for tasks should be atleast 1 and at most {self.tasks_limit}"
        )

        self.chunk_size: int = chunk_size * 1_024
        self.tasks: int = int(tasks)
        self.dir: Path = Path(dir)
        self.part_dir = Path(part_dir)
        self.part_extension: str = part_extension
        self.merge_buffer_size: int = (chunk_size if merge_buffer_size is None else merge_buffer_size) * 1_024
        self.client: httpx.AsyncClient = httpx.AsyncClient(**kwargs)
        """httpx AsyncClient"""
        self.client.headers.update(request_headers)

    def __repr__(self) -> str:
        return (
            rf"<{self.__module__}.{self.__class__.__name__} tasks={self.tasks} "
            rf'dir="{self.dir}", chunk_size_in_bytes={self.chunk_size}>'
        )

    def _generate_saved_to(self, filename: str, dir: Path, index: int | None = None) -> Path:
        filename, ext = os.path.splitext(filename)
        index = f".{index}" if index is not None else ""
        ext = ext if ext else ""

        return dir.joinpath(f"{filename}{index}{ext}")

    def _create_headers(self, bytes_offset: int) -> dict:
        new_headers = self.client.headers.copy()
        new_headers["Range"] = f"bytes={bytes_offset}-"
        return new_headers

    async def _call_progress_hook(self, progress_hook: callable, download_tracker: DownloadTracker) -> None:
        """Interacts with progress hook"""
        if progress_hook is None:
            return

        if asyncio.iscoroutinefunction(progress_hook):
            await progress_hook(download_tracker)

        else:
            progress_hook(download_tracker)
            # NOTE: Consider using status code to determine whether to proceed
            # with download process or not

    async def _merge_parts(
        self,
        file_parts: list[DownloadTracker],
        filename: Path,
        keep_parts: bool = False,
    ) -> Path:
        """Combines the separated download parts into one.

        Args:
            file_parts (list[DownloadTracker]): List of the separate files.
            filename (Path): Filename for saving the merged parts under.
            clear_parts (bool, optional): Whether to keep the download parts. Defaults to False.

        Returns:
            Path: Filepath to the merged parts.
        """

        save_to = self.dir.joinpath(filename)
        ordered_parts: list[DownloadTracker] = []

        for part in file_parts:
            assert part.saved_to.exists(), f"Part not found in downloaded path {part}"
            assert part.is_complete, f"Incomplete file part {part}"
            ordered_parts.insert(part.index, part)

        if len(file_parts) == 1:
            logger.info(f'Moving downloaded part to "{save_to}"')
            return Path(shutil.move(file_parts[0].saved_to, save_to))

        logger.info(f'Merging {len(file_parts)} file part{"s" if len(file_parts) > 1 else ""} to "{save_to}"')

        async with aiofiles.open(
            save_to,
            "wb",
        ) as fh:
            for part in ordered_parts:
                async with aiofiles.open(part.saved_to, "rb") as part_fh:
                    saved_size = 0
                    read_size = self.merge_buffer_size

                    while saved_size < part.expected_size:
                        chunk = await part_fh.read(min(read_size, part.expected_size - saved_size))
                        if not chunk:
                            break
                        await fh.write(chunk)
                        saved_size += len(chunk)

                if not keep_parts:
                    os.remove(part.saved_to)

        return save_to

    async def _downloader(
        self,
        download_tracker: DownloadTracker,
        progress_bar: CustomTqdm,
        progress_hook: callable,
    ) -> DownloadTracker:
        """Downloads each file part"""

        resume = False
        write_mode = "wb"

        match download_tracker.download_mode:
            case DownloadMode.AUTO:
                resume = download_tracker.saved_to.exists()

            case DownloadMode.RESUME:
                resume = download_tracker.saved_to.exists()

        if resume:
            write_mode = "ab"
            download_tracker.download_mode = DownloadMode.RESUME
            downloaded_size = os.path.getsize(download_tracker.saved_to)
            download_tracker.bytes_offset += downloaded_size
            download_tracker.update_downloaded_size(downloaded_size)
            progress_bar.n += self.bytes_to_mb(downloaded_size)
            progress_bar.last_print_t = time.time()
            progress_bar.last_print_n = progress_bar.n

        else:
            download_tracker.download_mode = DownloadMode.START

        logger.debug(
            f"Downloading file-part {download_tracker.index} "
            f"({get_filesize_string(download_tracker.downloaded_size)}/"
            f'{get_filesize_string(download_tracker.expected_size)}) to "{download_tracker.saved_to}" '
            f"resume - {resume}"
        )

        async with self.client.stream(
            "GET",
            url=download_tracker.url,
            headers=self._create_headers(download_tracker.bytes_offset),
        ) as stream:
            stream.raise_for_status()

            async with aiofiles.open(download_tracker.saved_to, write_mode) as fh:
                async for chunk in stream.aiter_bytes(self.chunk_size):
                    await fh.write(chunk)

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
        mode: DownloadMode = DownloadMode.AUTO,
        disable_progress_bar: bool = None,
        file_size: int = None,
        keep_parts: bool = False,
        suppress_incompatible_error: bool = False,
        timeout_retry_attempts: int = DEFAULT_READ_TIMEOUT_ATTEMPTS,
        retry_attempts_count: int = 0,
        colour: str = "cyan",
        simple: bool = False,
        test: bool = False,
        leave: bool = True,
        ascii: bool = False,
        **kwargs,
    ) -> DownloadedFile | httpx.Response:
        """Initiate download process of a file.

        Args:
            url (str): Url of the file to be downloaded.
            filename (str, optional): Filename for the downloaded content. Defaults to None.
            progress_hook (callable, optional): Function to call with the download progress information. Defaults to None.
            mode (DownloadMode, optional): Whether to start or resume incomplete download. Defaults DownloadMode.AUTO.
            disable_progress_bar (bool, optional): Do not show progress_bar. Defaults to None (decide based on progress_hook).
            file_size (int, optional): Size of the file to be downloaded. Defaults to None.
            keep_parts (bool, optional): Whether to retain the separate download parts. Defaults to False.
            suppress_incompatible_error (bool, optional): Do no raise error when response headers lack Etag. Defaults to False.
            timeout_retry_attempts (int, optional): Number of times to retry download upon read request timing out. Defaults to DEFAULT_READ_TIMEOUT_ATTEMPTS.
            leave (bool, optional): Keep all leaves of the progressbar. Defaults to True.
            colour (str, optional): Progress bar display color. Defaults to "cyan".
            simple (bool, optional): Show percentage and bar only in progressbar. Deafults to False.
            test (bool, optional): Just test if download is possible but do not actually download. Defaults to False.
            ascii (bool, optional): Use unicode (smooth blocks) to fill the progress-bar meter. Defaults to False.

        kwargs: Other keyword arguments for `tqdm.tdqm`

        Returns:
            DownloadedFile | httpx.Response: Downloaded file details or httpx Response incase of (test=True).
        """  # noqa: E501

        assert_instance(mode, DownloadMode)

        if progress_hook is not None:
            assert callable(progress_hook), (
                f"Value for progress_hook must be a function not {type(progress_hook)}"
            )

        async_task_items = []
        download_tracker_items = []

        if disable_progress_bar is None:
            disable_progress_bar = progress_hook is not None

        logger.debug(f'Initializing download (tasks - {self.tasks}) for file in url - "{url}"')

        async with self.client.stream("GET", url=url) as stream:
            stream.raise_for_status()

            if (
                stream.headers.get("Etag") is None
                and suppress_incompatible_error is False
                and self.tasks != 1
            ):
                raise IncompatibleServerError(
                    "Server response header lacks Etag value which means "
                    "it doesn't support resuming downloads. "
                    "Set tasks to 1 or activate suppress_incompatible_error parameter "
                    "to silence this error."
                )

            content_length = stream.headers.get("content-length", file_size)
            if type(content_length) is str:
                content_length = int(content_length)

            filename = filename or self.get_filename_from_header(stream.headers)

            if filename is None:
                # Try to get from path
                _, filename = os.path.split(urlparse(url).path)
                if not filename:
                    raise FilenameNotFoundError(
                        "Unable to get filename. Pass value using parameter filename to suppress this error"
                    )

            filename = sanitize_filename(filename)

            final_saved_to = self._generate_saved_to(filename, self.dir)

            if content_length is None:
                raise FilesizeNotFoundError(
                    "Unable to get the content-length of the file from server response. "
                    "Set the content-length using parameter file_size to suppres this error."
                )

            elif not test and final_saved_to.exists() and mode is not DownloadMode.START:
                if os.path.getsize(final_saved_to) == content_length:
                    logger.warning(f'Download already completed for the file in path "{final_saved_to}"')
                    return DownloadedFile(
                        url=url,
                        saved_to=final_saved_to,
                        size=os.path.getsize(final_saved_to),
                        duration=0,
                        file_parts=[],
                        merge_duration=0,
                        expected_size=content_length,
                    )

            size_with_unit = get_filesize_string(content_length)
            filename_disp = filename if len(filename) <= 8 + 3 else filename[:8] + "..."

            if test:
                logger.info(f"Download test passed successfully ({size_with_unit}) - {final_saved_to}")
                return stream

            logger.info(
                f"{'Starting' if retry_attempts_count == 0 else 'Resuming'} "
                f'download process ({self.tasks} tasks, {size_with_unit}) - "{filename}"'
            )
            p_bar = CustomTqdm(
                total=self.bytes_to_mb(content_length),
                desc=f"Downloading{f' [{filename_disp}]'}",
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

            for index, offset_load in enumerate(self.get_offset_load(content_length, self.tasks)):
                offset, load = offset_load
                download_tracker = DownloadTracker(
                    url=url,
                    saved_to=self._generate_saved_to(
                        f"{filename}-{offset, load}{self.part_extension}",
                        self.part_dir,
                        index,
                    ),
                    index=index,
                    bytes_offset=offset,
                    expected_size=load,
                    download_mode=mode,
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

            download_start_time = time.time()

            try:
                file_parts = await asyncio.gather(*async_task_items)

            except httpx.ReadTimeout as e:
                retry_attempts_count += 1

                if retry_attempts_count <= timeout_retry_attempts:
                    # Retry

                    p_bar.close()

                    logger.info(
                        f"Retrying download after read request timed out - "
                        f"attempt number ({retry_attempts_count}/{timeout_retry_attempts})"
                    )

                    return await self.run(
                        url=url,
                        filename=filename,
                        progress_hook=progress_hook,
                        mode=DownloadMode.AUTO,  # Changed
                        disable_progress_bar=disable_progress_bar,
                        file_size=file_size,
                        keep_parts=keep_parts,
                        suppress_incompatible_error=suppress_incompatible_error,
                        timeout_retry_attempts=timeout_retry_attempts,
                        retry_attempts_count=retry_attempts_count,
                        colour=colour,
                        simple=simple,
                        test=test,
                        leave=leave,
                        ascii=ascii,
                        **kwargs,
                    )

                else:
                    if timeout_retry_attempts:
                        logger.warning(
                            f"Giving up on download after exhausting all {timeout_retry_attempts} "
                            "read timeout retry attempts."
                        )

                    else:
                        logger.info(
                            "Download read request has timed out. In order to automatically retry the "
                            " process, declare value for retry attempts using parameter "
                            "timeout_retry_attempts"
                        )

                    raise e

            download_duration = time.time() - download_start_time

            merge_start_time = time.time()
            p_bar.close()

            saved_to = await self._merge_parts(file_parts, filename=filename, keep_parts=keep_parts)

            downloaded_file = DownloadedFile(
                url=url,
                saved_to=saved_to,
                expected_size=content_length,
                size=os.path.getsize(saved_to),
                file_parts=file_parts,
                merge_duration=time.time() - merge_start_time,
                duration=download_duration,
            )

            logger.info(
                f"Done downloading {get_filesize_string(downloaded_file.size)} "
                f"in {get_duration_string(downloaded_file.duration)} "
                f'saved to "{downloaded_file.saved_to}"'
            )

            return downloaded_file

    def run_sync(self, *args, **kwargs) -> DownloadedFile | httpx.Response:
        """Synchronously initiate download process of a file."""
        return asyncio.run(self.run(*args, **kwargs))
