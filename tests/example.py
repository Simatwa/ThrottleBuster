from throttlebuster import DownloadTracker, ThrottleBuster


async def callback_function(data: DownloadTracker):
    percent = (data.downloaded_size / data.expected_size) * 100
    print(f"> Downloading {data.saved_to.name} {percent:.2f}%", end="\r")


async def main(url: str):
    throttlebuster = ThrottleBuster(tasks=1)
    return await throttlebuster.run(
        url,
        # progress_hook=callback_function
    )


if __name__ == "__main__":
    import asyncio

    url = "http://localhost:8888/test.1.opus"

    out = asyncio.run(main(url))
    print(out)
