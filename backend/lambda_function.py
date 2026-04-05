"""Lambda entry point for the Omni Image API."""

from __future__ import annotations

from typing import Any

from mangum import Mangum

from src.app import app

handler = Mangum(app, lifespan="off")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler function."""
    return handler(event, context)  # type: ignore[return-value]
