"""Application configuration with dataclass and environment variable reading."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields

from dotenv import load_dotenv

from src.utils.exceptions import ConfigurationError

# Fields where None means "caller did not pass a value, read from env"
_ENV_OVERRIDE_FIELDS = frozenset({"rate_limit", "rate_limit_window", "is_lambda"})


@dataclass
class AppConfig:
    """Application configuration read from environment variables."""

    nova_image_bucket: str = ""
    aws_region: str = ""
    bedrock_region: str = ""
    nova_omni_model: str = "us.amazon.nova-2-omni-v1:0"
    bedrock_timeout: int = 120
    rate_limit: int = 10
    rate_limit_window: int = 3600
    log_level: str = ""
    allowed_origins: str = ""
    is_lambda: bool = False

    # Track which fields were explicitly set by the caller
    _explicit_fields: frozenset[str] | None = None

    def __init__(self, **kwargs: object) -> None:
        valid_fields = {f.name for f in fields(self) if f.name != "_explicit_fields"}
        unexpected = set(kwargs) - valid_fields
        if unexpected:
            raise TypeError(f"Unexpected AppConfig field(s): {', '.join(sorted(unexpected))}")

        object.__setattr__(
            self, "_explicit_fields", frozenset(kwargs.keys()) & _ENV_OVERRIDE_FIELDS
        )
        for f in fields(self):
            if f.name == "_explicit_fields":
                continue
            if f.name in kwargs:
                object.__setattr__(self, f.name, kwargs[f.name])
            else:
                object.__setattr__(self, f.name, f.default)
        self.__post_init__()

    def __post_init__(self) -> None:
        """Read env vars at instantiation time and validate."""
        explicit = self._explicit_fields or frozenset()

        if not self.nova_image_bucket:
            self.nova_image_bucket = os.getenv("NOVA_IMAGE_BUCKET", "")
        if not self.aws_region:
            self.aws_region = os.getenv("AWS_REGION", "us-west-2")
        if not self.bedrock_region:
            self.bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
        if not self.log_level:
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
        if not self.allowed_origins:
            self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")

        if "rate_limit" not in explicit:
            self.rate_limit = int(os.getenv("RATE_LIMIT", "10"))
        if "rate_limit_window" not in explicit:
            self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
        if "is_lambda" not in explicit:
            self.is_lambda = "AWS_LAMBDA_FUNCTION_NAME" in os.environ

        # Validation
        if not self.nova_image_bucket:
            raise ConfigurationError("NOVA_IMAGE_BUCKET is required")


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get or create the application config singleton."""
    global _config
    if _config is None:
        load_dotenv()
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset config for testing. Not for production use."""
    global _config
    _config = None
