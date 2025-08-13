"""Commandline module"""

# TODO: Add click to cli extras
import logging
import os
import sys

import click

from throttlebuster.constants import (
    CURRENT_WORKING_DIR,
    DOWNLOAD_PART_EXTENSION,
    THREADS_LIMIT,
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
    type=click.IntRange(1, THREADS_LIMIT),
    help="Number of threads to carry out the download : 2",
    default=2,
)
@click.option(
    "-C",
    "--chunk-size",
    type=click.INT,
    help="Streaming download chunk size in kilobytes : 256",
    default=256,
)
@click.option(
    "-D",
    "--dir",
    help="Directory for saving the downloaded file to : PWD",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
    default=CURRENT_WORKING_DIR,
)
@click.option(
    "-P",
    "--part-dir",
    help="Directory for temporarily saving the downloaded file-parts to : PWD",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
    default=CURRENT_WORKING_DIR,
)
@click.option(
    "-E",
    "--part-extension",
    help=f"Filename extension for download parts : {DOWNLOAD_PART_EXTENSION}",
    default=DOWNLOAD_PART_EXTENSION,
)
@click.option(
    "-H",
    "--request-headers",
    help="Httpx request headers : default",
    nargs=2,
    multiple=True,
)
@click.option(
    "-B",
    "--merge-buffer-size",
    type=click.IntRange(1, 102400),
    default=256,
    help="Buffer size for merging the separated files in kilobytes : 256",
)
@click.option("-F", "--filename", help="Filename for the downloaded content")
@click.option(
    "-M",
    "--download-mode",
    help="Whether to start or resume incomplete download : auto",
    type=click.Choice(DownloadMode.map().keys(), case_sensitive=False),
    default=DownloadMode.AUTO.value,
)
@click.option("-L", "--file_size", type=click.INT, help="Size of the file to be downloaded : None")
@click.option("-K", "--colour", default="cyan", help="Progress bar display color : cyan")
@click.option(
    "-k",
    "--keep-parts",
    is_flag=True,
    help="Whether to retain the separate download parts : False",
)
@click.option(
    "-s",
    "--simple",
    is_flag=True,
    help="Show percentage and bar only in progressbar : False",
)
@click.option(
    "-t",
    "--test",
    is_flag=True,
    help="Just test if download is possible but do not actually download : False",
)
@click.option(
    "-a",
    "--ascii",
    is_flag=True,
    help="Use unicode (smooth blocks) to fill the progress-bar meter : False",
)
@click.option(
    "-l",
    "--no-leave",
    help="Do not keep all leaves of the progressbar : False",
    is_flag=True,
)
@click.option(
    "-z",
    "--disable-progress-bar",
    is_flag=True,
    help="Do not show progress_bar : False",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Do not show any interactive information : False",
)
@click.option("-v", "--verbose", help="Show more detailed information : 0", count=True, default=0)
def download_command(
    threads: int,
    chunk_size: int,
    dir: str,
    part_dir: str,
    part_extension: str,
    request_headers: list[tuple[str]],
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
    )
    if quiet:
        run_kwargs["disable_progress_bar"] = True

    run_kwargs["leave"] = run_kwargs.get("no_leave") is False
    run_kwargs.pop("no_leave")
    run_kwargs["download_mode"] = DownloadMode.map().get(run_kwargs.get("download_mode"))

    throttlebuster.run_sync(**run_kwargs)


def main():
    """Entry point"""
    try:
        throttlebuster.add_command(download_command, "download")
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
