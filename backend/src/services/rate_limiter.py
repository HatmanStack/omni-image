"""Rate limiter with S3-backed tracking for distributed environments."""

from __future__ import annotations

import json
import time
from typing import Any, Final, TypedDict

from botocore.exceptions import ClientError

from src.models.config import get_config
from src.services.aws_client import AWSClientManager
from src.utils.exceptions import RateLimitError
from src.utils.logger import app_logger, log_performance


class RateLimitUsage(TypedDict):
    """Rate limit usage information."""

    total_requests: int
    limit: int
    remaining: int


class RateLimiter:
    """S3-backed rate limiter with optimistic locking."""

    S3_KEY: Final[str] = "rate-limit/requests.json"

    def __init__(self) -> None:
        self.client_manager = AWSClientManager()

    @log_performance
    def check_rate_limit(self) -> None:
        """Check if request should be rate limited.

        Raises:
            RateLimitError: If rate limit is exceeded.
        """
        try:
            allowed = self._check_and_increment()
            if not allowed:
                app_logger.warning("Rate limit exceeded")
                raise RateLimitError()
        except RateLimitError:
            raise
        except Exception as e:
            app_logger.error(
                f"Rate limiter fail-open: {type(e).__name__}: {e!s}. "
                "Request allowed despite rate limit check failure."
            )

    def _check_and_increment(self) -> bool:
        """Check rate limit and increment counter with optimistic locking."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                timestamps, etag = self._get_rate_data()
                current_time = time.time()
                window = get_config().rate_limit_window

                # Clean old entries
                timestamps = [t for t in timestamps if t > current_time - window]

                if len(timestamps) >= get_config().rate_limit:
                    return False

                timestamps.append(current_time)

                try:
                    self._put_rate_data(timestamps, etag)
                    app_logger.debug(
                        f"Rate check passed: {len(timestamps)}/{get_config().rate_limit}"
                    )
                    return True
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code == "PreconditionFailed" and attempt < max_retries - 1:
                        app_logger.debug(
                            f"Rate limit ETag conflict, retrying (attempt {attempt + 1})"
                        )
                        continue
                    raise

            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                    if self._try_initialize():
                        return True
                    continue
                app_logger.warning(
                    f"Rate limit S3 error (fail-open): "
                    f"{e.response.get('Error', {}).get('Code', 'unknown')}. "
                    "Request allowed."
                )
                return True  # Fail open

        app_logger.warning("Rate limit check exhausted retries, allowing request")
        return True

    def _get_rate_data(self) -> tuple[list[float], str]:
        """Get rate data and ETag from S3."""
        response = self.client_manager.s3_client.get_object(
            Bucket=get_config().nova_image_bucket,
            Key=self.S3_KEY,
        )

        etag = response.get("ETag", "")
        body = response["Body"].read().decode("utf-8")
        data: dict[str, Any] = json.loads(body)
        timestamps: list[float] = data.get("timestamps", [])
        return timestamps, etag

    def _put_rate_data(self, timestamps: list[float], etag: str = "") -> None:
        """Write rate data to S3 with optimistic locking."""
        kwargs: dict[str, Any] = {
            "Bucket": get_config().nova_image_bucket,
            "Key": self.S3_KEY,
            "Body": json.dumps({"timestamps": timestamps}),
            "ContentType": "application/json",
        }
        if etag:
            kwargs["IfMatch"] = etag
        self.client_manager.s3_client.put_object(**kwargs)

    def _try_initialize(self) -> bool:
        """Try to create the rate data file for the first request."""
        try:
            self.client_manager.s3_client.put_object(
                Bucket=get_config().nova_image_bucket,
                Key=self.S3_KEY,
                Body=json.dumps({"timestamps": [time.time()]}),
                ContentType="application/json",
                IfNoneMatch="*",
            )
            app_logger.info("Initialized rate limit data in S3")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("PreconditionFailed", "ConditionalCheckFailedException"):
                app_logger.debug("Race on rate data init, will retry via optimistic lock")
                return False
            app_logger.warning(f"Failed to initialize rate data: {e!s}")
            return True  # Fail open

    def get_current_usage(self) -> RateLimitUsage:
        """Get current rate limit usage for monitoring."""
        try:
            timestamps, _etag = self._get_rate_data()
            current_time = time.time()
            window = get_config().rate_limit_window
            timestamps = [t for t in timestamps if t > current_time - window]
            total = len(timestamps)

            return RateLimitUsage(
                total_requests=total,
                limit=get_config().rate_limit,
                remaining=max(0, get_config().rate_limit - total),
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                return self._empty_usage()
            app_logger.error(f"Failed to get current usage: {e!s}")
            return self._empty_usage()
        except Exception as e:
            app_logger.error(f"Failed to get current usage: {e!s}")
            return self._empty_usage()

    def _empty_usage(self) -> RateLimitUsage:
        """Return a zero-value usage dict for fallback responses."""
        return RateLimitUsage(
            total_requests=0,
            limit=get_config().rate_limit,
            remaining=get_config().rate_limit,
        )


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset rate limiter for testing. Not for production use."""
    global _rate_limiter
    _rate_limiter = None
