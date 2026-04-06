"""Bedrock Converse service for Nova 2 Omni image generation."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from src.models.config import get_config
from src.models.schemas import ConverseResult
from src.services.aws_client import AWSClientManager
from src.utils.exceptions import BedrockError
from src.utils.logger import app_logger, log_performance


class BedrockService:
    """Service for calling the Bedrock Converse API for Nova 2 Omni."""

    def __init__(self) -> None:
        self.client_manager = AWSClientManager()

    @log_performance
    def converse(
        self,
        messages: list[dict[str, Any]],
        inference_config: dict[str, Any] | None = None,
    ) -> ConverseResult:
        """Call the Bedrock Converse API and process the response.

        Args:
            messages: List of message dicts matching the Converse API format.
            inference_config: Optional dict with maxTokens, temperature, topP, topK.

        Returns:
            ConverseResult with extracted text, image, usage, and latency.

        Raises:
            BedrockError: On any failure communicating with Bedrock.
        """
        try:
            app_logger.info("Calling Bedrock Converse API")

            kwargs: dict[str, Any] = {
                "modelId": get_config().nova_omni_model,
                "messages": messages,
            }
            if inference_config:
                kwargs["inferenceConfig"] = inference_config

            response = self.client_manager.bedrock_client.converse(**kwargs)

            result = self._process_response(response)

            self._store_response(messages, result)

            return result

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            app_logger.error(f"Bedrock client error: {error_msg}")
            raise BedrockError("Image generation failed") from e
        except BedrockError:
            raise
        except Exception as e:
            app_logger.error(f"Unexpected error in converse: {e!s}")
            raise BedrockError("Image generation failed") from e

    def _process_response(self, response: Any) -> ConverseResult:
        """Process a Converse API response into a ConverseResult."""
        try:
            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])

            if not content:
                raise BedrockError("Empty response content from Converse API")

            text, image_bytes, image_format = self._process_content_blocks(content)

            usage = response.get("usage", {})
            metrics = response.get("metrics", {})
            latency_ms = metrics.get("latencyMs", 0)

            return ConverseResult(
                text=text,
                image_bytes=image_bytes,
                image_format=image_format,
                usage=usage,
                latency_ms=latency_ms,
            )

        except BedrockError:
            raise
        except Exception as e:
            raise BedrockError(f"Error processing response: {e!s}") from e

    def _process_content_blocks(
        self, content: list[dict[str, Any]]
    ) -> tuple[str | None, bytes | None, str]:
        """Extract text and image from content block list."""
        texts: list[str] = []
        image_bytes: bytes | None = None
        image_format = "png"

        for block in content:
            if "text" in block:
                texts.append(block["text"])
            elif "image" in block:
                img = block["image"]
                image_format = img.get("format", "png")
                source = img.get("source", {})
                image_bytes = source.get("bytes")

        text = " ".join(texts) if texts else None
        return text, image_bytes, image_format

    def _store_response(self, messages: list[dict[str, Any]], result: ConverseResult) -> None:
        """Store request and response to S3 for archival."""
        try:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S_%f")
            unique_id = uuid.uuid4().hex[:8]
            bucket = get_config().nova_image_bucket

            # Extract and store input images as separate files, replace bytes in messages with S3 keys
            sanitized_messages = self._extract_input_images(messages, bucket, timestamp, unique_id)

            # Store request JSON (no bytes remaining)
            request_key = f"requests/{timestamp}_{unique_id}_request.json"
            self.client_manager.s3_client.put_object(
                Bucket=bucket,
                Key=request_key,
                Body=json.dumps(sanitized_messages),
                ContentType="application/json",
            )

            # Store output image if present
            if result.image_bytes:
                image_key = f"images/{timestamp}_{unique_id}_output.{result.image_format}"
                self.client_manager.s3_client.put_object(
                    Bucket=bucket,
                    Key=image_key,
                    Body=result.image_bytes,
                    ContentType=f"image/{result.image_format}",
                )

            # Store text response
            response_key = f"responses/{timestamp}_{unique_id}_response.json"
            self.client_manager.s3_client.put_object(
                Bucket=bucket,
                Key=response_key,
                Body=json.dumps(
                    {
                        "text": result.text,
                        "usage": result.usage,
                        "latency_ms": result.latency_ms,
                    }
                ),
                ContentType="application/json",
            )

            app_logger.debug(f"Stored response and image to S3: {timestamp}")

        except Exception as e:
            app_logger.warning(f"Failed to store response to S3: {e!s}")

    def _extract_input_images(
        self,
        messages: list[dict[str, Any]],
        bucket: str,
        timestamp: str,
        unique_id: str,
    ) -> list[dict[str, Any]]:
        """Extract input images from messages, store as files, replace with S3 keys."""
        sanitized: list[dict[str, Any]] = []
        img_index = 0

        for msg in messages:
            new_msg: dict[str, Any] = {"role": msg["role"], "content": []}
            for block in msg.get("content", []):
                if "image" in block:
                    img = block["image"]
                    source = img.get("source", {})
                    image_bytes = source.get("bytes")
                    fmt = img.get("format", "png")
                    if isinstance(image_bytes, bytes):
                        image_key = f"images/{timestamp}_{unique_id}_input_{img_index}.{fmt}"
                        self.client_manager.s3_client.put_object(
                            Bucket=bucket,
                            Key=image_key,
                            Body=image_bytes,
                            ContentType=f"image/{fmt}",
                        )
                        new_msg["content"].append({"image": {"format": fmt, "s3_key": image_key}})
                        img_index += 1
                    else:
                        new_msg["content"].append(block)
                else:
                    new_msg["content"].append(block)
            sanitized.append(new_msg)

        return sanitized


_bedrock_service: BedrockService | None = None


def get_bedrock_service() -> BedrockService:
    """Get or create the BedrockService singleton."""
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
    return _bedrock_service


def reset_bedrock_service() -> None:
    """Reset BedrockService for testing. Not for production use."""
    global _bedrock_service
    _bedrock_service = None
