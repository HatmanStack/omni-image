"""Tests for Lambda function entry point."""

from unittest.mock import MagicMock, patch


class TestLambdaHandler:
    def test_lambda_handler_is_callable(self) -> None:
        from lambda_function import lambda_handler

        assert callable(lambda_handler)

    @patch("src.handlers.health.get_config")
    def test_health_via_lambda_handler(self, mock_config: MagicMock) -> None:
        from lambda_function import lambda_handler

        mock_cfg = MagicMock()
        mock_cfg.nova_omni_model = "us.amazon.nova-2-omni-v1:0"
        mock_cfg.bedrock_region = "us-west-2"
        mock_config.return_value = mock_cfg

        event = {
            "version": "2.0",
            "requestContext": {
                "http": {
                    "method": "GET",
                    "path": "/api/health",
                    "sourceIp": "127.0.0.1",
                    "protocol": "HTTP/1.1",
                },
                "accountId": "123456789012",
                "apiId": "api-id",
                "domainName": "test.execute-api.us-west-2.amazonaws.com",
                "domainPrefix": "test",
                "stage": "$default",
                "requestId": "test-request-id",
                "time": "01/Jan/2024:00:00:00 +0000",
                "timeEpoch": 1704067200000,
            },
            "rawPath": "/api/health",
            "rawQueryString": "",
            "headers": {
                "host": "test.execute-api.us-west-2.amazonaws.com",
            },
            "isBase64Encoded": False,
        }

        context = MagicMock()
        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
