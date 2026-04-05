"""AWS client management with thread-safe singleton and async storage."""

import atexit
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Final

import boto3
from botocore.config import Config

from src.models.config import get_config
from src.utils.exceptions import ConfigurationError
from src.utils.logger import app_logger

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_s3 import S3Client


class AWSClientManager:
    """Thread-safe singleton for AWS client management with connection pooling."""

    _instance: "AWSClientManager | None" = None
    _lock: threading.Lock = threading.Lock()
    _client_lock: threading.Lock = threading.Lock()

    _bedrock_client: "BedrockRuntimeClient | None" = None
    _s3_client: "S3Client | None" = None

    _executor: ThreadPoolExecutor | None = None
    MAX_WORKERS: Final[int] = 2

    def __new__(cls) -> "AWSClientManager":
        """Thread-safe singleton creation using double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._executor = ThreadPoolExecutor(max_workers=cls.MAX_WORKERS)
                    atexit.register(cls._shutdown_executor)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the client manager (only runs once due to singleton)."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            app_logger.info("Initializing AWS Client Manager")

    @classmethod
    def _shutdown_executor(cls) -> None:
        """Shutdown the thread pool executor on exit."""
        if cls._executor is not None:
            cls._executor.shutdown(wait=False)
            cls._executor = None

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton state for testing. Not for production use."""
        with cls._lock, cls._client_lock:
            if cls._executor is not None:
                cls._executor.shutdown(wait=False)
            cls._instance = None
            cls._bedrock_client = None
            cls._s3_client = None
            cls._executor = None

    @property
    def bedrock_client(self) -> "BedrockRuntimeClient":
        """Thread-safe lazy initialization of Bedrock client with connection pooling."""
        if self._bedrock_client is None:
            with self._client_lock:
                if self._bedrock_client is None:
                    try:
                        AWSClientManager._bedrock_client = boto3.client(
                            service_name="bedrock-runtime",
                            region_name=get_config().bedrock_region,
                            config=Config(
                                read_timeout=get_config().bedrock_timeout,
                                max_pool_connections=10,
                                retries={"max_attempts": 3},
                            ),
                        )
                        app_logger.info("Bedrock client initialized")
                    except Exception as e:
                        raise ConfigurationError(
                            f"Failed to initialize Bedrock client: {e!s}"
                        ) from e
        assert self._bedrock_client is not None
        return self._bedrock_client

    @property
    def s3_client(self) -> "S3Client":
        """Thread-safe lazy initialization of S3 client."""
        if self._s3_client is None:
            with self._client_lock:
                if self._s3_client is None:
                    try:
                        AWSClientManager._s3_client = boto3.client(
                            service_name="s3",
                            region_name=get_config().aws_region,
                            config=Config(max_pool_connections=5),
                        )
                        app_logger.info("S3 client initialized")
                    except Exception as e:
                        raise ConfigurationError(f"Failed to initialize S3 client: {e!s}") from e
        assert self._s3_client is not None
        return self._s3_client

    @property
    def executor(self) -> ThreadPoolExecutor | None:
        """Get the thread pool executor for async operations."""
        return self._executor
