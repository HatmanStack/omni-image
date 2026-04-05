"""Tests for custom exception hierarchy."""

from src.utils.exceptions import (
    BedrockError,
    ConfigurationError,
    OmniImageError,
    RateLimitError,
    StorageError,
)


class TestOmniImageError:
    def test_default_message(self) -> None:
        err = OmniImageError("something went wrong")
        assert str(err) == "something went wrong"
        assert err.message == "something went wrong"

    def test_error_code_none_by_default(self) -> None:
        err = OmniImageError("test")
        assert err.error_code is None

    def test_custom_error_code(self) -> None:
        err = OmniImageError("test", error_code="CUSTOM")
        assert err.error_code == "CUSTOM"


class TestRateLimitError:
    def test_default_message(self) -> None:
        err = RateLimitError()
        assert err.message == "Rate limit exceeded"
        assert err.error_code == "RATE_LIMIT_EXCEEDED"

    def test_custom_message(self) -> None:
        err = RateLimitError("custom limit msg")
        assert err.message == "custom limit msg"

    def test_inheritance(self) -> None:
        err = RateLimitError()
        assert isinstance(err, OmniImageError)
        assert isinstance(err, Exception)


class TestConfigurationError:
    def test_default_message(self) -> None:
        err = ConfigurationError()
        assert err.message == "Configuration error"
        assert err.error_code == "CONFIG_ERROR"

    def test_custom_message(self) -> None:
        err = ConfigurationError("missing bucket")
        assert err.message == "missing bucket"

    def test_inheritance(self) -> None:
        assert isinstance(ConfigurationError(), OmniImageError)


class TestBedrockError:
    def test_default_message(self) -> None:
        err = BedrockError()
        assert err.message == "Bedrock service error"
        assert err.error_code == "BEDROCK_ERROR"

    def test_custom_message(self) -> None:
        err = BedrockError("model timeout")
        assert err.message == "model timeout"

    def test_inheritance(self) -> None:
        assert isinstance(BedrockError(), OmniImageError)


class TestStorageError:
    def test_default_message(self) -> None:
        err = StorageError()
        assert err.message == "Storage error"
        assert err.error_code == "STORAGE_ERROR"

    def test_custom_message(self) -> None:
        err = StorageError("S3 unreachable")
        assert err.message == "S3 unreachable"

    def test_inheritance(self) -> None:
        assert isinstance(StorageError(), OmniImageError)
