"""Tests for S3-backed rate limiter."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.utils.exceptions import RateLimitError


class TestRateLimiter:
    def setup_method(self) -> None:
        from src.services.aws_client import AWSClientManager
        from src.services.rate_limiter import reset_rate_limiter

        reset_rate_limiter()
        AWSClientManager._reset()

    def teardown_method(self) -> None:
        from src.services.aws_client import AWSClientManager
        from src.services.rate_limiter import reset_rate_limiter

        reset_rate_limiter()
        AWSClientManager._reset()

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_request_allowed_under_limit(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()
        mock_mgr.s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({"timestamps": [now - 100]}).encode()),
            "ETag": '"etag1"',
        }

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()  # should not raise

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_rate_limit_exceeded(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()
        timestamps = [now - i * 10 for i in range(10)]
        mock_mgr.s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({"timestamps": timestamps}).encode()),
            "ETag": '"etag1"',
        }

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        with pytest.raises(RateLimitError):
            limiter.check_rate_limit()

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_old_entries_cleaned(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()
        # 9 old entries (outside window) + 1 recent
        timestamps = [now - 7200] * 9 + [now - 100]
        mock_mgr.s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({"timestamps": timestamps}).encode()),
            "ETag": '"etag1"',
        }

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()  # should pass (only 1 recent entry)

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_etag_conflict_triggers_retry(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()
        mock_mgr.s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({"timestamps": [now - 100]}).encode()),
            "ETag": '"etag1"',
        }
        # First put fails with PreconditionFailed, second succeeds
        mock_mgr.s3_client.put_object.side_effect = [
            ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "ETag mismatch"}},
                "PutObject",
            ),
            {},
        ]

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()  # should retry and succeed

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_no_such_key_triggers_initialization(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            "GetObject",
        )

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()  # should initialize and succeed

        # Verify put_object was called with IfNoneMatch
        put_calls = mock_mgr.s3_client.put_object.call_args_list
        assert any(call.kwargs.get("IfNoneMatch") == "*" for call in put_calls)

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_init_race_condition(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()

        # First get: NoSuchKey, init fails (race), second get succeeds
        mock_mgr.s3_client.get_object.side_effect = [
            ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
                "GetObject",
            ),
            {
                "Body": MagicMock(read=lambda: json.dumps({"timestamps": [now - 100]}).encode()),
                "ETag": '"etag2"',
            },
        ]
        mock_mgr.s3_client.put_object.side_effect = [
            ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "Already exists"}},
                "PutObject",
            ),
            {},  # second put succeeds
        ]

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_fail_open_on_unexpected_error(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "S3 is down"}},
            "GetObject",
        )

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.check_rate_limit()  # should not raise (fail-open)

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_get_current_usage(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        now = time.time()
        timestamps = [now - 100, now - 200, now - 300]
        mock_mgr.s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({"timestamps": timestamps}).encode()),
            "ETag": '"etag1"',
        }

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        usage = limiter.get_current_usage()
        assert usage["total_requests"] == 3
        assert usage["limit"] == 10
        assert usage["remaining"] == 7

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_get_current_usage_no_such_key(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            "GetObject",
        )

        from src.services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        usage = limiter.get_current_usage()
        assert usage["total_requests"] == 0
        assert usage["remaining"] == 10

    @patch("src.services.rate_limiter.AWSClientManager")
    def test_singleton_behavior(self, mock_aws_cls: MagicMock) -> None:
        from src.services.rate_limiter import get_rate_limiter, reset_rate_limiter

        reset_rate_limiter()
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2
