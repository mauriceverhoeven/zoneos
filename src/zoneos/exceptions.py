"""Custom exceptions for ZoneOS."""


class ZoneOSError(Exception):
    """Base exception for ZoneOS errors."""

    pass


class SpeakerNotFoundError(ZoneOSError):
    """Raised when a speaker cannot be found."""

    pass


class NoSpeakersAvailableError(ZoneOSError):
    """Raised when no speakers are available."""

    pass


class FavoriteNotFoundError(ZoneOSError):
    """Raised when a favorite cannot be found."""

    pass


class InvalidIndexError(ZoneOSError):
    """Raised when an invalid index is provided."""

    pass


class GroupOperationError(ZoneOSError):
    """Raised when a group operation fails."""

    pass


class PlaybackError(ZoneOSError):
    """Raised when playback operations fail."""

    pass
