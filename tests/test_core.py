import os

import pytest

from tests import DOWNLOAD_DIR, FILE_URL, PART_DIR
from throttlebuster import DownloadedFile, DownloadMode, ThrottleBuster


@pytest.mark.asyncio
async def test_download_test():
    throttlebuster = ThrottleBuster(dir=DOWNLOAD_DIR, part_dir=PART_DIR)
    response = await throttlebuster.run(FILE_URL, test=True)
    assert response.is_success


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=["tasks_amount"],
    argvalues=[
        (1,),
        (2,),
        (3,),
    ],
)
async def test_real_download(tasks_amount: int):
    throttlebuster = ThrottleBuster(
        dir=DOWNLOAD_DIR,
        part_dir=PART_DIR,
        tasks=tasks_amount,
    )
    downloaded_file = await throttlebuster.run(
        FILE_URL, mode=DownloadMode.START, disable_progress_bar=True
    )
    assert downloaded_file.saved_to.exists()
    assert downloaded_file.tasks_used == tasks_amount
    assert downloaded_file.is_complete


@pytest.mark.asyncio
async def test_different_tasks_time():
    downloaded_file_items: list[DownloadedFile] = []

    for task in range(1, 5):
        # Ensure file size is big enough or throttling is small enough
        # for time difference to be noticed
        throttlebuster = ThrottleBuster(
            dir=DOWNLOAD_DIR, part_dir=PART_DIR, tasks=task
        )
        downloaded_file = await throttlebuster.run(
            FILE_URL, mode=DownloadMode.START, disable_progress_bar=True
        )
        assert downloaded_file.is_complete

        for file_part in downloaded_file.file_parts:
            assert file_part.is_complete

        if downloaded_file_items:
            previous_dowloaded_file = downloaded_file_items[-1]
            assert (
                downloaded_file.duration < previous_dowloaded_file.duration
            )

        downloaded_file_items.append(downloaded_file)

        os.remove(downloaded_file.saved_to)
