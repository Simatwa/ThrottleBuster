"""Error module"""


class ThrottleBusterException(Exception):
    """Base class for exceptions"""


class FilenameNotFoundError(ThrottleBusterException):
    """Raised when server response.headers does not contain
    `content-disposition` and user has not declared the filename value.
    """


class FilesizeNotFoundError(ThrottleBusterException):
    """Raised when server response.headers does not contain
    `content-length` and user has not declared the value for filename."""


class IncompatibleServerError(ThrottleBusterException):
    """Raised when server response lacks Etag in the headers"""
