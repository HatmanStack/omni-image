"""Tests for application logger."""

import pytest

from src.utils.logger import AppLogger, app_logger, log_performance


class TestAppLogger:
    def test_log_info(self) -> None:
        logger = AppLogger()
        logger.info("test message")  # should not raise

    def test_log_debug(self) -> None:
        logger = AppLogger()
        logger.debug("debug message")

    def test_log_warning(self) -> None:
        logger = AppLogger()
        logger.warning("warning message")

    def test_log_error(self) -> None:
        logger = AppLogger()
        logger.error("error message")

    def test_log_with_invalid_level_defaults_to_info(self) -> None:
        logger = AppLogger()
        # Should not raise, should default to INFO
        logger.log("test", level="INVALID_LEVEL")

    def test_app_logger_is_singleton_instance(self) -> None:
        assert isinstance(app_logger, AppLogger)


class TestLogPerformance:
    def test_decorator_logs_timing(self) -> None:
        @log_performance
        def dummy_func() -> str:
            return "result"

        result = dummy_func()
        assert result == "result"

    def test_decorator_raises_on_error(self) -> None:
        @log_performance
        def failing_func() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func()

    def test_decorator_preserves_function_name(self) -> None:
        @log_performance
        def my_func() -> None:
            pass

        assert my_func.__name__ == "my_func"
