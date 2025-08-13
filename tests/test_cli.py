import subprocess

import pytest


def run_system_command(command: str) -> int:
    try:
        result = subprocess.run(
            "python -m throttlebuster " + command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(e, e.output, sep="\n")
        return e.returncode


def test_version():
    returncode = run_system_command("--version")
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["download --help"],
        ["estimate --help"],
    ],
)
def test_help(command):
    returncode = run_system_command(command)
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["download http://localhost:8888/miel-martin.webm --test"],
        ["download http://localhost:8888/miel-martin.webm --test --threads 3"],
    ],
)
def test_download(command):
    returncode = run_system_command(command)
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["estimate --url http://localhost:8888/miel-martin.webm 500000"],
        ["estimate --size 1010029 300000"],
        ["estimate --url http://localhost:8888/miel-martin.webm 500000 --json"],
        ["estimate --size 1010029 300000 --json"],
    ],
)
def test_estimate(command):
    returncode = run_system_command(command)
    assert returncode <= 0
