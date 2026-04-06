"""Optimized logging with thread safety."""

import logging
import os
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class OptimizedLogger:
    """Thread-safe logger. Lambda streams stdout/stderr to CloudWatch automatically."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _is_lambda() -> bool:
        """Check if running in Lambda."""
        return bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    _VALID_LEVELS: frozenset[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

    def log(self, message: str, level: str = "INFO", request_id: str = "") -> None:
        """Log message at the given level."""
        if level.upper() not in self._VALID_LEVELS:
            level = "INFO"
        prefix = f"[{request_id}] " if request_id else ""
        getattr(self.logger, level.lower())(f"{prefix}{message}")

    def debug(self, message: str, request_id: str = "") -> None:
        """Log at DEBUG level."""
        self.log(message, "DEBUG", request_id=request_id)

    def info(self, message: str, request_id: str = "") -> None:
        """Log at INFO level."""
        self.log(message, "INFO", request_id=request_id)

    def warning(self, message: str, request_id: str = "") -> None:
        """Log at WARNING level."""
        self.log(message, "WARNING", request_id=request_id)

    def error(self, message: str, request_id: str = "") -> None:
        """Log at ERROR level."""
        self.log(message, "ERROR", request_id=request_id)


# Global logger instance
app_logger = OptimizedLogger()


def log_performance(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to log function performance."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"

        app_logger.debug(f"Starting {func_name}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            app_logger.info(f"Completed {func_name} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            app_logger.error(f"Failed {func_name} after {duration:.2f}s: {e!s}")
            raise

    return wrapper
