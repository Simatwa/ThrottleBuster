"""Commandline module"""

# TODO: Add click to cli extras
import logging
import os
import sys

import click

from throttlebuster.constants import (
    CURRENT_WORKING_DIR,
    DEFAULT_THREADS,
    DEFAULT_THREADS_LIMIT,
    DOWNLOAD_PART_EXTENSION,
    DownloadMode,
)

DEBUG = os.getenv("BEGUG", "0") == "1"

command_context_settings = dict(auto_envvar_prefix="THROTTLEBUSTER")


def prepare_start(quiet: bool, verbose: bool) -> None:
    """Set up some stuff for better CLI usage such as:

    - Set higher logging level for some packages.
    ...

    """
    if verbose > 3:
        verbose = 2
    logging.basicConfig(
        format=("[%(asctime)s] : %(levelname)s - %(message)s" if verbose else "[%(module)s] %(message)s"),
        datefmt="%d-%b-%Y %H:%M:%S",
        level=(
            logging.ERROR
            if quiet
            # just a hack to ensure
            #           -v -> INFO
            #           -vv -> DEBUG
            else (30 - (verbose * 10))
            if verbose > 0
            else logging.INFO
        ),
    )
    # logging.info(f"Using host url - {HOST_URL}")
    packages = ("httpx",)
    for package_name in packages:
        package_logger = logging.getLogger(package_name)
        package_logger.setLevel(logging.WARNING)


@click.group()
@click.version_option(package_name="throttlebuster")
def throttlebuster():
    """Accelerate file downloads by overcoming common throttling restrictions
    envvar-prefix : THROTTLEBUSTER."""


@click.command(context_settings=command_context_settings)
@click.argument("url")
@click.option(
    "-T",
    "--threads",
    type=click.IntRange(1, DEFAULT_THREADS_LIMIT),
    help="Number of threads to carry out the download",
    default=DEFAULT_THREADS,
    show_default=True,
)
@click.option(
    "-Z",
    "--chunk-size",
    type=click.INT,
    help="Streaming download chunk size in kilobytes",
    default=256,
    show_default=True,
)
@click.option(
    "-D",
    "--dir",
    help="Directory for saving the downloaded file to",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
    default=CURRENT_WORKING_DIR,
    show_default=True,
)
@click.option(
    "-P",
    "--part-dir",
    help="Directory for temporarily saving the downloaded file-parts to",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
    default=CURRENT_WORKING_DIR,
    show_default=True,
)
@click.option(
    "-E",
    "--part-extension",
    help="Filename extension for download parts",
    default=DOWNLOAD_PART_EXTENSION,
    show_default=True,
)
@click.option(
    "-H",
    "--request-headers",
    help="Httpx request header - [key value] : default",
    nargs=2,
    multiple=True,
)
@click.option(
    "-C",
    "--request-cookies",
    help="Httpx request cookie - [key value]: default",
    nargs=2,
    multiple=True,
)
@click.option(
    "-B",
    "--merge-buffer-size",
    type=click.IntRange(1, 102400),
    default=256,
    help="Buffer size for merging the separated files in kilobytes",
    show_default=True,
)
@click.option("-F", "--filename", help="Filename for the downloaded content")
@click.option(
    "-M",
    "--mode",
    help="Whether to start or resume incomplete download",
    type=click.Choice(DownloadMode.map().keys(), case_sensitive=False),
    default=DownloadMode.AUTO.value,
    show_default=True,
)
@click.option("-L", "--file-size", type=click.INT, help="Size of the file to be downloaded")
@click.option(
    "-K",
    "--colour",
    default="cyan",
    help="Progress bar display color",
    show_default=True,
)
@click.option(
    "-k",
    "--keep-parts",
    is_flag=True,
    help="Whether to retain the separate download parts",
)
@click.option(
    "-s",
    "--simple",
    is_flag=True,
    help="Show percentage and bar only in progressbar",
)
@click.option(
    "-t",
    "--test",
    is_flag=True,
    help="Just test if download is possible but do not actually download",
)
@click.option(
    "-a",
    "--ascii",
    is_flag=True,
    help="Use unicode (smooth blocks) to fill the progress-bar meter",
)
@click.option(
    "-l",
    "--no-leave",
    help="Do not keep all leaves of the progressbar",
    is_flag=True,
)
@click.option(
    "-z",
    "--disable-progress-bar",
    is_flag=True,
    help="Do not show progress_bar",
)
@click.option(
    "-i",
    "--suppress-incompatible-error",
    help="Do no raise error when response headers lack Etag",
    is_flag=True,
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Do not show any interactive information",
)
@click.option(
    "-v",
    "--verbose",
    help="Show more detailed information",
    count=True,
    default=0,
    show_default=True,
)
def download_command(
    threads: int,
    chunk_size: int,
    dir: str,
    part_dir: str,
    part_extension: str,
    request_headers: list[tuple[str]],
    request_cookies: list[tuple[str]],
    merge_buffer_size: int,
    quiet: bool,
    verbose: int,
    **run_kwargs,
):
    """Download file using http protocol"""
    prepare_start(quiet, verbose)

    from throttlebuster import ThrottleBuster

    throttlebuster = ThrottleBuster(
        dir=dir,
        chunk_size=chunk_size,
        threads=threads,
        part_dir=part_dir,
        part_extension=part_extension,
        merge_buffer_size=merge_buffer_size,
        request_headers=request_headers,
        cookies=list(request_cookies),
    )
    if quiet:
        run_kwargs["disable_progress_bar"] = True

    run_kwargs["leave"] = run_kwargs.get("no_leave") is False
    run_kwargs.pop("no_leave")
    run_kwargs["mode"] = DownloadMode.map().get(run_kwargs.get("mode"))

    throttlebuster.run_sync(**run_kwargs)


@click.command(context_settings=command_context_settings)
@click.argument("throttle", type=click.INT)
@click.option(
    "-U",
    "--url",
    help="Url to the target file",
)
@click.option("-S", "--size", type=click.INT, help="Size in bytes of the targeted file")
@click.option(
    "-T",
    "--threads",
    help="Threads amount to base the estimate on : Range (2-30)",
    type=click.IntRange(1, DEFAULT_THREADS_LIMIT),
)
@click.option("-j", "--json", is_flag=True, help="Stdout estimates in json format")
def estimate_command(throttle: int, url: str | None, size: int, threads: int, json: bool):
    """Estimate download duration for different threads"""
    assert size or url, "Either size of the file (--size) or url to it (--url) is required."

    import rich

    from throttlebuster.helpers import get_duration_string, get_filesize_string

    if size:
        size_in_bytes = size

    elif url:
        from throttlebuster import ThrottleBuster

        throttle_buster = ThrottleBuster()
        response = throttle_buster.run_sync(url, test=True)
        size_in_bytes = int(response.headers.get("content-length"))

    estimates: list[tuple[str]] = []

    def update_estimates(thread: int):
        load_per_thread = size_in_bytes / thread
        download_duration = load_per_thread / throttle
        download_duration_string = get_duration_string(download_duration)
        load_per_thread_string = get_filesize_string(load_per_thread)
        estimates.append((str(thread), download_duration_string, load_per_thread_string))

    if threads is None:
        for thread in range(2, 21):
            update_estimates(thread)
        estimates.reverse()

    else:
        update_estimates(threads)

    if json:
        rich.print_json(data=dict(estimates=estimates), indent=4)

    else:
        from rich.table import Table

        table = Table(
            "Threads",
            "Duration",
            "Load per thread",
            title=(f"{get_filesize_string(size_in_bytes)} at {get_filesize_string(throttle)}/s"),
            show_lines=False,
        )
        for row in estimates:
            table.add_row(*row)

        rich.print(table)


def main():
    """Entry point"""
    try:
        throttlebuster.add_command(download_command, "download")
        throttlebuster.add_command(estimate_command, "estimate")
        sys.exit(throttlebuster())

    except Exception as e:
        exception_msg = str({e.args[1] if e.args and len(e.args) > 1 else e})

        if DEBUG:
            logging.exception(e)
        else:
            if bool(exception_msg):
                logging.error(exception_msg)
            # sys.exit(show_any_help(e, exception_msg))

        sys.exit(1)
