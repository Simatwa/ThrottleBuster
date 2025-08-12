from throttlebuster import DownloadTracker, ThrottleBuster


async def callback_function(data: DownloadTracker):
    percent = (data.downloaded_size / data.expected_size) * 100
    print(f"> Downloading {data.saved_to.name} {percent:.2f}%", end="\r")


if __name__ == "__main__":
    import asyncio

    downloader = ThrottleBuster()

    # url = "http://localhost:8000/file/blob.opus"
    # url = "http://192.168.204.58:8000/files/test.webm"
    url = "http://192.168.204.58:8000/files/test.mp4"
    out = asyncio.run(
        downloader.run(
            url,
            progress_hook=callback_function,
        )
    )
    print(out)
