"""Application configuration with dataclass and environment variable reading."""

from __future__ import annotations

_config: object | None = None


def get_config() -> object:
    """Get or create the application config singleton. Placeholder until Task 4."""
    raise NotImplementedError("Config not yet implemented")


def reset_config() -> None:
    """Reset config for testing. Not for production use."""
    global _config
    _config = None
