""""""

import logging
from importlib import metadata

try:
    __version__ = metadata.version("throttlebuster")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Smartwa"
__repo__ = "https://github.com/Simatwa/throttlebuster"

logger = logging.getLogger(__name__)

from throttlebuster.core import ThrottleBuster  # noqa: E402
from throttlebuster.models import DownloadTracker  # noqa: E402

__all__ = [
    "ThrottleBuster",
    "DownloadTracker",
]
