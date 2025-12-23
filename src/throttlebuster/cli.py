"""Commandline module"""

# TODO: Add click to cli extras
import logging
import os
import sys

import click

from throttlebuster.constants import (
    CURRENT_WORKING_DIR,
    DEFAULT_READ_TIMEOUT_ATTEMPTS,
    DEFAULT_TASKS,
    DEFAULT_TASKS_LIMIT,
    DOWNLOAD_PART_EXTENSION,
    DownloadMode,
)

DEBUG = os.getenv("BEGUG", "0") == "1"

command_context_settings = dict(auto_envvar_prefix="THROTTLEBUSTER")


def prepare_start(quiet: bool, verbose: bool) -> None:
    """Set up some stuff for better CLI usage such as:

    - Setting higher logging level for some packages.
    ...

    """
    if verbose > 3:
        verbose = 2
    logging.basicConfig(
        format=(
            "[%(asctime)s] : %(levelname)s - %(message)s"
            if verbose
            else "[%(module)s] %(message)s"
        ),
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
    """Accelerate file downloads by overcoming throttling restrictions
    envvar-prefix : THROTTLEBUSTER."""


@click.command(context_settings=command_context_settings)
@click.argument("url")
@click.option(
    "-T",
    "--tasks",
    type=click.IntRange(1, DEFAULT_TASKS_LIMIT),
    help="Number of tasks to carry out the download",
    default=DEFAULT_TASKS,
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
    type=click.Path(
        exists=True, file_okay=False, writable=True, resolve_path=True
    ),
    default=CURRENT_WORKING_DIR,
    show_default=True,
)
@click.option(
    "-P",
    "--part-dir",
    help="Directory for temporarily saving the downloaded file-parts to",
    type=click.Path(
        exists=True, file_okay=False, writable=True, resolve_path=True
    ),
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
@click.option(
    "-F", "--filename", help="Filename for the downloaded content"
)
@click.option(
    "-M",
    "--mode",
    help="Whether to start or resume incomplete download",
    type=click.Choice(DownloadMode.map().keys(), case_sensitive=False),
    default=DownloadMode.AUTO.value,
    show_default=True,
)
@click.option(
    "-L",
    "--file-size",
    type=click.INT,
    help="Size of the file to be downloaded",
)
@click.option(
    "-X",
    "--proxy",
    help="Request proxy with schema of any type [default: system-set]",
)
@click.option(
    "-R",
    "--timeout-retry-attempts",
    type=click.INT,
    help="Number of times to retry download upon read request timing out",
    show_default=True,
    default=DEFAULT_READ_TIMEOUT_ATTEMPTS,
)
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
    help="Do not keep traces of the progressbar",
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
    "--follow-redirects/--no-follow-redirects",
    help="Follow url redirects by the server",
    default=False,
    show_default=True,
)
@click.option(
    "--verify/--no-verify",
    default=True,
    help="Verify server certificate",
    show_default=True,
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
    tasks: int,
    chunk_size: int,
    dir: str,
    part_dir: str,
    part_extension: str,
    request_headers: list[tuple[str]],
    request_cookies: list[tuple[str]],
    merge_buffer_size: int,
    quiet: bool,
    verbose: int,
    follow_redirects: bool,
    verify: bool,
    proxy: str | None,
    **run_kwargs,
):
    """Download file using http(s) protocol"""
    prepare_start(quiet, verbose)

    from throttlebuster import ThrottleBuster

    throttlebuster = ThrottleBuster(
        dir=dir,
        chunk_size=chunk_size,
        tasks=tasks,
        part_dir=part_dir,
        part_extension=part_extension,
        merge_buffer_size=merge_buffer_size,
        request_headers=request_headers,
        cookies=list(request_cookies),
        # Httpx args
        follow_redirects=follow_redirects,
        verify=verify,
        proxy=proxy,
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
@click.option(
    "-S",
    "--size",
    type=click.INT,
    help="Size in bytes of the targeted file",
)
@click.option(
    "-T",
    "--tasks",
    help="Tasks amount to base the estimate on",
    type=click.IntRange(1, DEFAULT_TASKS_LIMIT),
)
@click.option(
    "-j", "--json", is_flag=True, help="Stdout estimates in json format"
)
def estimate_command(
    throttle: int, url: str | None, size: int, tasks: int, json: bool
):
    """Estimate download duration for different task amount"""
    assert size or url, (
        "Either size of the file (--size) or url to it (--url) is "
        "required."
    )

    import rich

    from throttlebuster.helpers import (
        get_duration_string,
        get_filesize_string,
    )

    if size:
        size_in_bytes = size

    elif url:
        from throttlebuster import ThrottleBuster

        throttle_buster = ThrottleBuster()
        response = throttle_buster.run_sync(url, test=True)
        size_in_bytes = int(response.headers.get("content-length"))

    estimates: list[tuple[str]] = []

    def update_estimates(task: int):
        load_per_task = size_in_bytes / task
        download_duration = load_per_task / throttle
        download_duration_string = get_duration_string(download_duration)
        load_per_task_string = get_filesize_string(load_per_task)
        estimates.append(
            (str(task), download_duration_string, load_per_task_string)
        )

    if tasks is None:
        for task in range(1, 21):
            update_estimates(task)
        estimates.reverse()

    else:
        update_estimates(tasks)

    if json:
        rich.print_json(data=dict(estimates=estimates), indent=4)

    else:
        from rich.table import Table

        table = Table(
            "Tasks",
            "Duration",
            "Load per task",
            title=(
                f"{get_filesize_string(size_in_bytes)} at "
                f"{get_filesize_string(throttle)}/s"
            ),
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

        throttlebuster.add_command(download_command, "d")
        throttlebuster.add_command(estimate_command, "e")

        sys.exit(throttlebuster())

    except Exception as e:
        exception_msg = str(
            {e.args[1] if e.args and len(e.args) > 1 else e}
        )

        if DEBUG:
            logging.exception(e)
        else:
            if bool(exception_msg):
                logging.error(exception_msg)
            # sys.exit(show_any_help(e, exception_msg))

        sys.exit(1)
