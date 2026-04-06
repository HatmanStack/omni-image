"""Tests for optimized logger."""

import os
from unittest.mock import patch

import pytest

from src.utils.logger import OptimizedLogger, app_logger, log_performance


class TestOptimizedLogger:
    def test_log_info(self) -> None:
        logger = OptimizedLogger()
        logger.info("test message")  # should not raise

    def test_log_debug(self) -> None:
        logger = OptimizedLogger()
        logger.debug("debug message")

    def test_log_warning(self) -> None:
        logger = OptimizedLogger()
        logger.warning("warning message")

    def test_log_error(self) -> None:
        logger = OptimizedLogger()
        logger.error("error message")

    def test_log_with_invalid_level_defaults_to_info(self) -> None:
        logger = OptimizedLogger()
        # Should not raise, should default to INFO
        logger.log("test", level="INVALID_LEVEL")

    def test_is_lambda_true(self) -> None:
        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-function"}):
            assert OptimizedLogger._is_lambda() is True

    def test_is_lambda_false(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AWS_LAMBDA_FUNCTION_NAME", None)
            assert OptimizedLogger._is_lambda() is False

    def test_app_logger_is_singleton_instance(self) -> None:
        assert isinstance(app_logger, OptimizedLogger)


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
