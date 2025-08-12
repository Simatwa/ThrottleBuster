""""""

from importlib import metadata

try:
    __version__ = metadata.version("throttlebuster")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Smartwa"
__repo__ = "https://github.com/Simatwa/throttlebuster"


from throttlebuster.constants import DownloadMode
from throttlebuster.core import ThrottleBuster
from throttlebuster.helpers import logger
from throttlebuster.models import DownloadedFile, DownloadTracker

__all__ = ["ThrottleBuster", "DownloadTracker", "DownloadedFile", "DownloadMode", "logger"]
