"""Project-wide exception type."""


class ZplusError(Exception):
    """Raised when z-plus cannot continue, e.g. unrecoverable syntax or a bad path."""
