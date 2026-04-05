"""Tests for application configuration."""

import os
from unittest.mock import patch

import pytest

from src.utils.exceptions import ConfigurationError


class TestAppConfig:
    def test_successful_creation_with_env_vars(self) -> None:
        from src.models.config import get_config

        config = get_config()
        assert config.nova_image_bucket == "test-bucket"
        assert config.aws_region == "us-west-2"
        assert config.bedrock_region == "us-west-2"

    def test_missing_bucket_raises_configuration_error(self) -> None:
        from src.models.config import AppConfig, reset_config

        reset_config()
        with patch.dict(os.environ, {"NOVA_IMAGE_BUCKET": ""}, clear=False):
            os.environ.pop("NOVA_IMAGE_BUCKET", None)
            with pytest.raises(ConfigurationError, match="NOVA_IMAGE_BUCKET is required"):
                AppConfig()

    def test_default_values(self) -> None:
        from src.models.config import get_config

        config = get_config()
        assert config.rate_limit == 10
        assert config.rate_limit_window == 3600
        assert config.bedrock_timeout == 120
        assert config.nova_omni_model == "us.amazon.nova-2-omni-v1:0"
        assert config.log_level == "INFO"
        assert config.allowed_origins == "*"

    def test_env_var_override_rate_limit(self) -> None:
        from src.models.config import AppConfig, reset_config

        reset_config()
        with patch.dict(os.environ, {"RATE_LIMIT": "20", "NOVA_IMAGE_BUCKET": "test-bucket"}):
            config = AppConfig()
            assert config.rate_limit == 20

    def test_env_var_override_log_level(self) -> None:
        from src.models.config import AppConfig, reset_config

        reset_config()
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG", "NOVA_IMAGE_BUCKET": "test-bucket"}):
            config = AppConfig()
            assert config.log_level == "DEBUG"

    def test_singleton_behavior(self) -> None:
        from src.models.config import get_config

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_singleton(self) -> None:
        from src.models.config import get_config, reset_config

        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_is_lambda_detection(self) -> None:
        from src.models.config import AppConfig, reset_config

        reset_config()
        with patch.dict(
            os.environ,
            {"AWS_LAMBDA_FUNCTION_NAME": "my-func", "NOVA_IMAGE_BUCKET": "test-bucket"},
        ):
            config = AppConfig()
            assert config.is_lambda is True

    def test_is_lambda_false_when_not_set(self) -> None:
        from src.models.config import get_config

        os.environ.pop("AWS_LAMBDA_FUNCTION_NAME", None)
        config = get_config()
        assert config.is_lambda is False

    def test_explicit_kwargs_override_env_vars(self) -> None:
        from src.models.config import AppConfig, reset_config

        reset_config()
        config = AppConfig(
            nova_image_bucket="explicit-bucket",
            rate_limit=50,
        )
        assert config.nova_image_bucket == "explicit-bucket"
        assert config.rate_limit == 50
