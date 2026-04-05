"""Custom exceptions for the Omni Image application."""


class OmniImageError(Exception):
    """Base exception for Omni Image application."""

    def __init__(self, message: str = "An error occurred", error_code: str | None = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class RateLimitError(OmniImageError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


class ConfigurationError(OmniImageError):
    """Exception raised for configuration issues."""

    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(message, "CONFIG_ERROR")


class BedrockError(OmniImageError):
    """Exception raised for AWS Bedrock service errors."""

    def __init__(self, message: str = "Bedrock service error") -> None:
        super().__init__(message, "BEDROCK_ERROR")


class StorageError(OmniImageError):
    """Exception raised for S3 storage failures."""

    def __init__(self, message: str = "Storage error") -> None:
        super().__init__(message, "STORAGE_ERROR")
