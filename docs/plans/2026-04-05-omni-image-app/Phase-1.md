# Phase 1 -- Backend Implementation

## Phase Goal

Build the complete Python backend: a FastAPI Lambda function that receives chat messages
(text and images), calls the Bedrock Converse API for Nova 2 Omni image generation, stores
inputs/outputs to S3, and enforces S3-backed rate limiting. Also create the SAM template,
deploy script, CI pipeline, and project scaffolding.

**Success criteria:**

- All backend tests pass with >= 75% coverage
- `ruff check` and `ruff format --check` pass with zero errors
- `mypy --strict` passes with zero errors
- SAM template validates (`sam validate`)
- Deploy script runs interactively and deploys the stack

**Estimated tokens:** ~45,000

## Prerequisites

- Phase 0 read and understood
- Python >= 3.11 and uv installed
- AWS SAM CLI installed
- Node.js >= 20 installed (for deploy script and root package.json)

## Tasks

### Task 1: Project Scaffolding and Root Configuration

**Goal:** Create the monorepo directory structure, root package.json, .gitignore, and
backend Python project configuration.

**Files to Create:**

- `package.json` -- Root workspace with deploy script
- `.gitignore` -- Comprehensive ignore for Python, Node, SAM, env files
- `backend/pyproject.toml` -- Python project config (dependencies, ruff, mypy, pytest)
- `backend/src/__init__.py` -- Empty init
- `backend/src/handlers/__init__.py` -- Empty init
- `backend/src/models/__init__.py` -- Empty init
- `backend/src/services/__init__.py` -- Empty init
- `backend/src/utils/__init__.py` -- Empty init
- `backend/tests/__init__.py` -- Empty init
- `backend/tests/conftest.py` -- Shared test fixtures

**Implementation Steps:**

1. Create the root `package.json` with:
   - `name`: `omni-image`
   - `scripts.deploy`: `node scripts/deploy.js`
   - No dependencies (deploy script uses only Node.js built-ins)
1. Create `.gitignore` covering:
   - Python: `__pycache__/`, `.venv/`, `*.pyc`, `.mypy_cache/`, `.ruff_cache/`,
     `.pytest_cache/`, `.coverage`, `htmlcov/`
   - Node: `node_modules/`, `dist/`, `.svelte-kit/`, `build/`
   - SAM: `.aws-sam/`
   - Env: `.env`, `.env.*`, `!.env.example`
   - IDE: `.vscode/`, `.idea/`
   - OS: `.DS_Store`
1. Create `backend/pyproject.toml` following the canvas-demo pattern:
   - `requires-python = ">=3.11"`
   - Dependencies: `fastapi`, `mangum`, `boto3`, `python-dotenv`, `pydantic`
   - Dev dependencies: `pytest`, `pytest-cov`, `ruff`, `mypy`, `httpx`,
     `boto3-stubs[s3,bedrock-runtime,logs]`
   - Ruff config: same rules as canvas-demo (E, W, F, I, B, C4, UP, SIM, TCH, PTH, RUF),
     `line-length = 100`, `target-version = "py311"`, `src = ["src", "tests"]`
   - Mypy config: strict mode, same overrides as canvas-demo
   - Pytest config: `testpaths = ["tests"]`, markers for `unit` and `integration`
   - Coverage: `source = ["src"]`, `fail_under = 75`
1. Create all `__init__.py` files (empty)
1. Create `backend/tests/conftest.py` with:
   - Environment variable setup at module level (before any app imports):
     `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `NOVA_IMAGE_BUCKET`,
     `BEDROCK_REGION`
   - Autouse fixture `_reset_config_between_tests` that calls `reset_config()` before
     and after each test
   - `mock_config` fixture that patches env vars and returns config
   - `mock_s3_client` fixture returning a MagicMock with common S3 operations
   - `mock_converse_response` fixture returning a realistic Converse API response with
     both text and image content blocks
   - `mock_converse_text_only_response` fixture returning a text-only response

**Verification Checklist:**

- [x] `cd backend && uv sync` installs all dependencies without errors
- [x] `cd backend && uv run ruff check src/ tests/` passes
- [x] `cd backend && uv run mypy src/` passes (no source files yet, but config validates)
- [x] `cd backend && uv run pytest tests/` passes (no tests yet, but conftest loads)
- [x] Root `package.json` is valid JSON

**Testing Instructions:**

No tests to write for this task -- it is pure scaffolding. The conftest.py fixtures will
be exercised by tests in subsequent tasks.

**Commit Message Template:**

```text
chore(root): scaffold monorepo structure and backend project config

- Create root package.json with deploy script entry
- Create backend pyproject.toml with deps, ruff, mypy, pytest config
- Create backend directory structure with __init__.py files
- Create test conftest.py with shared fixtures
- Create .gitignore for Python, Node, SAM, env files
```

---

### Task 2: Custom Exception Hierarchy

**Goal:** Create the custom exception hierarchy for the application, following the
canvas-demo pattern but adapted for Omni Image (no NSFW errors, no image processing errors).

**Files to Create:**

- `backend/src/utils/exceptions.py`

**Files to Modify:**

- None

**Prerequisites:**

- Task 1 complete

**Implementation Steps:**

1. Create `backend/src/utils/exceptions.py` with:
   - `OmniImageError(Exception)` -- base exception with `message: str` and optional
     `error_code: str | None` attributes. Constructor calls `super().__init__(self.message)`
   - `RateLimitError(OmniImageError)` -- default message "Rate limit exceeded", error code
     `"RATE_LIMIT_EXCEEDED"`
   - `ConfigurationError(OmniImageError)` -- default message "Configuration error", error
     code `"CONFIG_ERROR"`
   - `BedrockError(OmniImageError)` -- default message "Bedrock service error", error code
     `"BEDROCK_ERROR"`
   - `StorageError(OmniImageError)` -- default message "Storage error", error code
     `"STORAGE_ERROR"`. Used for S3 storage failures that should be surfaced (not the
     fire-and-forget archival)

**Verification Checklist:**

- [x] `ruff check backend/src/utils/exceptions.py` passes
- [x] `mypy backend/src/utils/exceptions.py` passes
- [x] All exception classes are importable

**Testing Instructions:**

Write `backend/tests/test_exceptions.py`:

- Test that each exception can be instantiated with default message
- Test that each exception can be instantiated with custom message
- Test that `error_code` attribute is set correctly
- Test inheritance chain (e.g., `isinstance(RateLimitError("x"), OmniImageError)`)

Run: `cd backend && uv run pytest tests/test_exceptions.py -v`

**Commit Message Template:**

```text
feat(backend): add custom exception hierarchy

- Create OmniImageError base exception with message and error_code
- Add RateLimitError, ConfigurationError, BedrockError, StorageError
- Add unit tests for all exception classes
```

---

### Task 3: Logger Module

**Goal:** Create the logging module with CloudWatch integration, following the canvas-demo
pattern. The logger batches logs to CloudWatch in Lambda environments and falls back to
standard Python logging locally.

**Files to Create:**

- `backend/src/utils/logger.py`

**Prerequisites:**

- Task 2 complete (exceptions are imported in logger)

**Implementation Steps:**

1. Create `backend/src/utils/logger.py` following the canvas-demo `logger.py` closely:
   - `OptimizedLogger` class with:
     - `log_group` defaulting to `"/aws/lambda/omni-image"`
     - `log_stream` set to `"Omni-Stream"`
     - Thread-safe batch flushing with `_stream_lock` and `_batch_lock`
     - `_is_lambda()` static method checking `AWS_LAMBDA_FUNCTION_NAME` env var
     - Lazy `cloudwatch_client` property that imports `AWSClientManager` to avoid
       circular imports
     - `log()`, `debug()`, `info()`, `warning()`, `error()` methods
     - `_flush_logs()` and `_flush_logs_unlocked()` for CloudWatch batch writes
     - `__del__` that flushes remaining logs
   - Module-level `app_logger = OptimizedLogger()` singleton
   - `log_performance` decorator that logs start, completion time, and errors for
     decorated functions

**Verification Checklist:**

- [x] `ruff check backend/src/utils/logger.py` passes
- [x] `mypy backend/src/utils/logger.py` passes
- [x] `app_logger` is importable and callable

**Testing Instructions:**

Write `backend/tests/test_logger.py`:

- Test `log()` with various levels (DEBUG, INFO, WARNING, ERROR)
- Test `log()` with invalid level defaults to INFO
- Test `_is_lambda()` returns True/False based on env var
- Test `log_performance` decorator logs timing
- Test that CloudWatch batching is skipped when not in Lambda
- Mock `AWSClientManager` to avoid real AWS calls

Run: `cd backend && uv run pytest tests/test_logger.py -v`

**Commit Message Template:**

```text
feat(backend): add optimized logger with CloudWatch batching

- Create OptimizedLogger with thread-safe batch flushing
- Add log_performance decorator for function timing
- Add unit tests for logging and performance decorator
```

---

### Task 4: Application Configuration

**Goal:** Create the dataclass-based configuration module that reads from environment
variables, following the canvas-demo pattern but adapted for Omni Image settings.

**Files to Create:**

- `backend/src/models/config.py`

**Prerequisites:**

- Task 2 complete (imports ConfigurationError)

**Implementation Steps:**

1. Create `backend/src/models/config.py` following the canvas-demo `config.py` pattern:
   - `AppConfig` dataclass with fields:
     - `nova_image_bucket: str = ""` -- S3 bucket name
     - `aws_region: str = ""` -- Lambda/general AWS region
     - `bedrock_region: str = ""` -- Region for Bedrock API (default `"us-west-2"`)
     - `nova_omni_model: str = "us.amazon.nova-2-omni-v1:0"` -- Model ID
     - `bedrock_timeout: int = 120` -- Read timeout for Bedrock calls in seconds
     - `rate_limit: int = 10` -- Max requests per window
     - `rate_limit_window: int = 3600` -- Window size in seconds (60 minutes)
     - `log_level: str = ""` -- Log level (default from env or "INFO")
     - `allowed_origins: str = ""` -- Comma-separated CORS origins (default `"*"`)
     - `is_lambda: bool = False` -- Whether running in Lambda
   - Use the same `_ENV_OVERRIDE_FIELDS` pattern from canvas-demo for fields that can be
     overridden from env or passed explicitly
   - `__post_init__` reads env vars:
     - `NOVA_IMAGE_BUCKET` (required)
     - `AWS_REGION` (default `"us-west-2"`)
     - `BEDROCK_REGION` (default `"us-west-2"`)
     - `RATE_LIMIT` (default `"10"`)
     - `RATE_LIMIT_WINDOW` (default `"3600"`)
     - `LOG_LEVEL` (default `"INFO"`)
     - `ALLOWED_ORIGINS` (default `"*"`)
     - `AWS_LAMBDA_FUNCTION_NAME` presence sets `is_lambda`
   - Validation: `NOVA_IMAGE_BUCKET` is required (raise `ConfigurationError` if empty)
   - Note: Unlike canvas-demo, there are NO `aws_access_key_id`/`aws_secret_access_key`
     fields. The Lambda uses IAM role credentials (injected by the runtime), not explicit
     keys. boto3 picks up credentials automatically from the Lambda execution role
     environment. This is a deliberate simplification over canvas-demo, which used explicit
     keys because it ran on Amplify Hosting's container runtime where IAM roles were not
     available.
   - Module-level singleton: `_config`, `get_config()`, `reset_config()`

**Verification Checklist:**

- [x] `ruff check backend/src/models/config.py` passes
- [x] `mypy backend/src/models/config.py` passes
- [x] `get_config()` raises `ConfigurationError` when `NOVA_IMAGE_BUCKET` is not set
- [x] `reset_config()` clears the singleton

**Testing Instructions:**

Write `backend/tests/test_config.py`:

- Test successful config creation with all env vars set
- Test `ConfigurationError` when `NOVA_IMAGE_BUCKET` is missing
- Test default values (rate_limit=10, bedrock_region="us-west-2", etc.)
- Test env var override for `RATE_LIMIT`, `LOG_LEVEL`, etc.
- Test singleton behavior (`get_config()` returns same instance)
- Test `reset_config()` clears the cached instance
- Test explicit kwargs override env vars

Run: `cd backend && uv run pytest tests/test_config.py -v`

**Commit Message Template:**

```text
feat(backend): add dataclass configuration with env var reading

- Create AppConfig dataclass with Omni Image settings
- Read from environment variables with validation
- Add singleton pattern with get_config/reset_config
- Add unit tests for config creation, defaults, and validation
```

---

### Task 5: AWS Client Manager

**Goal:** Create the thread-safe singleton AWS client manager for Bedrock and S3, following
the canvas-demo pattern but using the Converse API and IAM role credentials.

**Files to Create:**

- `backend/src/services/aws_client.py`

**Prerequisites:**

- Task 3 (logger) and Task 4 (config) complete

**Implementation Steps:**

1. Create `backend/src/services/aws_client.py` following canvas-demo's `aws_client.py`:
   - `AWSClientManager` class with:
     - Thread-safe singleton via `__new__` with double-checked locking
     - `_bedrock_client` and `_s3_client` class-level attributes (no logs client needed --
       the logger handles CloudWatch directly)
     - `ThreadPoolExecutor` for async S3 storage operations
     - `bedrock_client` property: lazy init with `boto3.client("bedrock-runtime")` using
       `region_name=get_config().bedrock_region` and `Config(read_timeout=...,
       max_pool_connections=10, retries={"max_attempts": 3})`
     - `s3_client` property: lazy init with `boto3.client("s3")` using
       `region_name=get_config().aws_region`
     - Note: NO explicit `aws_access_key_id`/`aws_secret_access_key` parameters. boto3
       picks up credentials from the Lambda execution role automatically.
     - `_reset()` classmethod for testing
     - `_shutdown_executor()` classmethod registered with `atexit`
   - Use `TYPE_CHECKING` guard for mypy-boto3 type imports:
     `from mypy_boto3_bedrock_runtime import BedrockRuntimeClient`
     `from mypy_boto3_s3 import S3Client`

**Verification Checklist:**

- [x] `ruff check backend/src/services/aws_client.py` passes
- [x] `mypy backend/src/services/aws_client.py` passes
- [x] Singleton returns the same instance on multiple calls
- [x] `_reset()` clears all cached clients

**Testing Instructions:**

Write `backend/tests/test_aws_client.py`:

- Test singleton behavior (two instantiations return same object)
- Test `_reset()` clears the singleton
- Test `bedrock_client` property creates client with correct region (mock `boto3.client`)
- Test `s3_client` property creates client (mock `boto3.client`)
- Test `ConfigurationError` propagation when config is invalid
- Test thread safety is not violated (basic sanity -- call from two threads, verify same
  instance)

Run: `cd backend && uv run pytest tests/test_aws_client.py -v`

**Commit Message Template:**

```text
feat(backend): add thread-safe AWS client manager singleton

- Create AWSClientManager with Bedrock and S3 client properties
- Implement double-checked locking for thread safety
- Add ThreadPoolExecutor for async operations
- Add unit tests for singleton, client creation, and reset
```

---

### Task 6: Bedrock Converse Service

**Goal:** Create the service that calls the Bedrock Converse API for Nova 2 Omni, processes
responses containing text and images, and stores responses to S3 asynchronously.

**Files to Create:**

- `backend/src/services/bedrock_service.py`

**Prerequisites:**

- Task 5 (AWS client manager) complete

**Implementation Steps:**

1. Create `backend/src/services/bedrock_service.py`:
   - `BedrockService` class with:
     - `__init__` stores `AWSClientManager()` instance
     - `converse(messages, inference_config)` method:
       - `messages` is a list of message dicts matching the Converse API format (role +
         content blocks)
       - `inference_config` is an optional dict with `maxTokens`, `temperature`, `topP`,
         `topK`
       - Calls `self.client_manager.bedrock_client.converse(modelId=...,
         messages=messages, inferenceConfig=inference_config)` (only pass
         `inferenceConfig` if not None/empty)
       - Processes response: extracts `output.message.content` which is a list of content
         blocks. Each block is either `{"text": "..."}` or
         `{"image": {"format": "png", "source": {"bytes": <bytes>}}}`
       - Returns a `ConverseResult` dataclass containing:
         - `text: str | None` -- extracted text (concatenated from all text blocks)
         - `image_bytes: bytes | None` -- extracted image bytes (first image block)
         - `image_format: str` -- always "png" for Omni
         - `usage: dict` -- token usage from response
         - `latency_ms: int` -- from response metrics
       - Calls `_store_response_async()` for archival
       - Raises `BedrockError` on any failure
     - `_store_response_async(messages, result)` -- submits to thread pool executor
     - `_store_response_sync(messages, result)` -- stores to S3:
       - Request: `requests/{timestamp}_{uuid}_request.json` (the messages list)
       - Image: `images/{timestamp}_{uuid}_output.png` (if image in response)
       - Text: `responses/{timestamp}_{uuid}_response.json` (text + usage metadata)
     - `_process_content_blocks(content)` -- helper to extract text and image from
       content block list
   - Module-level singleton: `_bedrock_service`, `get_bedrock_service()`,
     `reset_bedrock_service()`
   - The `ConverseResult` dataclass should be in a new file
     `backend/src/models/schemas.py` (also used by the handler layer)

**Files to Also Create:**

- `backend/src/models/schemas.py` -- Pydantic models and dataclasses for API
  request/response shapes

**Verification Checklist:**

- [x] `ruff check backend/src/services/bedrock_service.py` passes
- [x] `mypy backend/src/services/bedrock_service.py` passes
- [x] Converse API is called with correct model ID and message format
- [x] Text and image are correctly extracted from response content blocks
- [x] S3 storage is fire-and-forget (errors logged but not raised)

**Testing Instructions:**

Write `backend/tests/test_bedrock_service.py`:

- Test `converse()` with text-only response
- Test `converse()` with text + image response
- Test `converse()` with image-only response (no text block)
- Test `converse()` raises `BedrockError` on `ClientError`
- Test `converse()` raises `BedrockError` on unexpected response format
- Test `_store_response_async()` submits to executor
- Test `_store_response_sync()` stores correct S3 keys
- Test S3 storage failure is logged but does not raise
- Test `inference_config` is omitted from API call when None
- Mock `AWSClientManager` and its `bedrock_client`/`s3_client` properties

Add to `backend/tests/conftest.py`:

- `mock_converse_response` fixture: returns a dict matching the Converse API response
  format with both text and image content blocks (image bytes as raw bytes, not base64)
- `mock_converse_text_only_response` fixture: text block only

Run: `cd backend && uv run pytest tests/test_bedrock_service.py -v`

**Commit Message Template:**

```text
feat(backend): add Bedrock Converse service for Nova 2 Omni

- Create BedrockService with converse() method
- Process mixed text+image response content blocks
- Add async S3 storage for request/response archival
- Create ConverseResult dataclass and API schemas
- Add unit tests for all response scenarios
```

---

### Task 7: Rate Limiter

**Goal:** Create the S3-backed rate limiter, adapted from canvas-demo with simplified
single-tier counting and configurable window.

**Files to Create:**

- `backend/src/services/rate_limiter.py`

**Prerequisites:**

- Task 5 (AWS client manager) complete

**Implementation Steps:**

1. Create `backend/src/services/rate_limiter.py` following canvas-demo's pattern but
   simplified:
   - `RateLimiter` class with:
     - `S3_KEY = "rate-limit/requests.json"` -- the S3 object key
     - `__init__` stores `AWSClientManager()` instance
     - `check_rate_limit()` method:
       - Calls `_check_and_increment()`
       - Raises `RateLimitError` if limit exceeded
       - Fail-open on unexpected errors (log warning, allow request)
     - `_check_and_increment()` -- optimistic locking loop (max 3 retries):
       - `_get_rate_data()` returns `(list[float], str)` -- list of timestamps + ETag
       - Clean old entries (remove timestamps older than
         `get_config().rate_limit_window` seconds)
       - If `len(timestamps) >= get_config().rate_limit`, return False
       - Append current timestamp, `_put_rate_data()` with ETag
       - On `PreconditionFailed`, retry
       - On `NoSuchKey`, call `_try_initialize()`
     - `_get_rate_data()` -- GET from S3, returns `(timestamps_list, etag)`
     - `_put_rate_data(timestamps, etag)` -- PUT to S3 with `IfMatch`
     - `_try_initialize()` -- PUT with `IfNoneMatch="*"` for first request
     - `get_current_usage()` -- returns a `RateLimitUsage` dict with `total_requests`,
       `limit`, `remaining`
   - Data format in S3 is simply `{"timestamps": [1234567890.123, ...]}` (no
     premium/standard distinction)
   - Module-level singleton: `_rate_limiter`, `get_rate_limiter()`, `reset_rate_limiter()`

**Verification Checklist:**

- [x] `ruff check backend/src/services/rate_limiter.py` passes
- [x] `mypy backend/src/services/rate_limiter.py` passes
- [x] Rate limit is enforced at configured threshold
- [x] Old entries are cleaned on each check
- [x] Optimistic locking retries on ETag conflict
- [x] Fail-open behavior on S3 errors

**Testing Instructions:**

Write `backend/tests/test_rate_limiter.py`:

- Test request allowed when under limit
- Test `RateLimitError` raised when at limit
- Test old entries are cleaned (timestamps outside window)
- Test ETag conflict triggers retry
- Test `NoSuchKey` triggers initialization
- Test initialization race condition (PreconditionFailed on init)
- Test fail-open on unexpected S3 error
- Test `get_current_usage()` returns correct counts
- Test `get_current_usage()` returns zeros on NoSuchKey
- Test singleton behavior
- Mock `AWSClientManager().s3_client` for all tests

Run: `cd backend && uv run pytest tests/test_rate_limiter.py -v`

**Commit Message Template:**

```text
feat(backend): add S3-backed rate limiter with optimistic locking

- Create RateLimiter with configurable window and limit
- Implement optimistic locking with ETag-based concurrency
- Add fail-open behavior on S3 errors
- Add unit tests for rate limiting, cleanup, and edge cases
```

---

### Task 8: API Request/Response Schemas

**Goal:** Define the Pydantic models for the API request and response payloads. These are
used by the FastAPI handler for automatic validation.

**Files to Create/Modify:**

- `backend/src/models/schemas.py` (extend from Task 6 if already created)

**Prerequisites:**

- Task 6 complete (ConverseResult exists)

**Implementation Steps:**

1. Add to `backend/src/models/schemas.py`:
   - **Request models** (Pydantic `BaseModel`):
     - `ContentBlock` -- union type: either `TextBlock(text=str)` or
       `ImageBlock(image=ImageSource)` where `ImageSource` has `format: str` and
       `data: str` (base64-encoded bytes)
     - `Message` -- `role: Literal["user", "assistant"]` and
       `content: list[TextBlock | ImageBlock]`
     - `InferenceConfig` -- optional fields: `maxTokens: int | None`,
       `temperature: float | None`, `topP: float | None`, `topK: int | None`
     - `ChatRequest` -- `messages: list[Message]`,
       `inferenceConfig: InferenceConfig | None = None`
   - **Response models**:
     - `ChatResponse` -- `text: str | None`, `image: str | None` (base64-encoded PNG),
       `usage: dict | None`, `latency_ms: int | None`
     - `ErrorResponse` -- `error: str`, `error_code: str`
     - `HealthResponse` -- `status: str`, `model: str`, `region: str`
     - `UsageResponse` -- `total_requests: int`, `limit: int`, `remaining: int`

**Verification Checklist:**

- [x] `ruff check backend/src/models/schemas.py` passes
- [x] `mypy backend/src/models/schemas.py` passes
- [x] Pydantic models validate correctly (required fields, optional fields, type coercion)
- [x] Base64 image data round-trips correctly

**Testing Instructions:**

Write `backend/tests/test_schemas.py`:

- Test `ChatRequest` validation with valid payload
- Test `ChatRequest` validation rejects missing `messages`
- Test `Message` accepts both text and image content blocks
- Test `InferenceConfig` all-optional fields
- Test `ChatResponse` serialization with and without image
- Test `ErrorResponse` serialization

Run: `cd backend && uv run pytest tests/test_schemas.py -v`

**Commit Message Template:**

```text
feat(backend): add Pydantic request/response schemas

- Create ChatRequest with Message and ContentBlock models
- Create ChatResponse, ErrorResponse, HealthResponse, UsageResponse
- Add InferenceConfig with optional Converse API parameters
- Add unit tests for validation and serialization
```

---

### Task 9: FastAPI Application and Handlers

**Goal:** Create the FastAPI application with route handlers for chat, health check, and
rate limit usage endpoints. Wire up CORS middleware, exception handlers, and the Mangum
Lambda adapter.

**Files to Create:**

- `backend/src/handlers/chat.py` -- Chat endpoint handler
- `backend/src/handlers/health.py` -- Health check handler
- `backend/src/app.py` -- FastAPI app creation and configuration
- `backend/lambda_function.py` -- Lambda entry point (Mangum wrapper)

**Prerequisites:**

- Tasks 6, 7, 8 complete

**Implementation Steps:**

1. Create `backend/src/app.py`:
   - `create_app()` function that:
     - Creates `FastAPI(title="Omni Image API", version="1.0.0")`
     - Adds CORS middleware with `allowed_origins` from config (split by comma)
     - Registers exception handlers:
       - `RateLimitError` -> 429 response with `ErrorResponse`
       - `BedrockError` -> 502 response with `ErrorResponse`
       - `OmniImageError` -> 500 response with `ErrorResponse`
       - Generic `Exception` -> 500 response with generic error message
     - Includes routers from `chat` and `health` handler modules
     - Returns the app
   - Module-level `app = create_app()` for Mangum to import

1. Create `backend/src/handlers/health.py`:
   - FastAPI `APIRouter` with prefix `/api`
   - `GET /health` -- returns `HealthResponse` with status, model ID, and region
   - `GET /usage` -- returns `UsageResponse` from rate limiter's `get_current_usage()`

1. Create `backend/src/handlers/chat.py`:
   - FastAPI `APIRouter` with prefix `/api`
   - `POST /chat` -- accepts `ChatRequest` body:
     - Call `get_rate_limiter().check_rate_limit()`
     - Convert the frontend message format to Converse API format:
       - For each message, convert `TextBlock` content to `{"text": "..."}` and
         `ImageBlock` content to `{"image": {"format": fmt, "source": {"bytes": <decoded>}}}`
       - Decode base64 image data to bytes for the Converse API
     - Build `inference_config` dict from request (only include non-None fields)
     - Call `get_bedrock_service().converse(messages, inference_config)`
     - Convert `ConverseResult` to `ChatResponse`:
       - If `image_bytes` present, base64-encode for the JSON response
       - Include text, usage, latency_ms
     - Return `ChatResponse`

1. Create `backend/lambda_function.py`:
   - Import `Mangum` and the FastAPI `app` from `src.app`
   - `handler = Mangum(app, lifespan="off")`
   - `def lambda_handler(event, context): return handler(event, context)`

**Verification Checklist:**

- [x] `ruff check backend/src/handlers/ backend/src/app.py backend/lambda_function.py` passes
- [x] `mypy backend/src/ backend/lambda_function.py` passes
- [x] Health endpoint returns 200 with correct schema
- [x] Chat endpoint returns 200 with text and/or image
- [x] Chat endpoint returns 429 when rate limited
- [x] Chat endpoint returns 502 on Bedrock errors
- [x] CORS headers are present in responses
- [x] Lambda handler is callable

**Testing Instructions:**

Write `backend/tests/test_handlers.py`:

- Use `httpx.AsyncClient` with `ASGITransport` and the FastAPI `app` for all tests
- Test `GET /api/health` returns 200 with model and region
- Test `GET /api/usage` returns 200 with rate limit info
- Test `POST /api/chat` with text-only message returns text response
- Test `POST /api/chat` with text+image message returns image response
- Test `POST /api/chat` returns 429 when rate limited (mock rate limiter to raise)
- Test `POST /api/chat` returns 502 when Bedrock fails (mock bedrock service to raise)
- Test `POST /api/chat` with invalid request body returns 422
- Test CORS headers are present
- Mock `get_bedrock_service()` and `get_rate_limiter()` in all chat tests

Write `backend/tests/test_lambda_function.py`:

- Test that `lambda_handler` is callable
- Test with a mock API Gateway v2 event for `GET /api/health`

Run: `cd backend && uv run pytest tests/test_handlers.py tests/test_lambda_function.py -v`

**Commit Message Template:**

```text
feat(backend): add FastAPI app with chat, health, and usage endpoints

- Create FastAPI app with CORS, exception handlers, and routers
- Add POST /api/chat endpoint with Bedrock and rate limit integration
- Add GET /api/health and GET /api/usage endpoints
- Add Mangum Lambda handler wrapper
- Add unit tests for all endpoints and error scenarios
```

---

### Task 10: SAM Template

**Goal:** Create the AWS SAM template that defines the Lambda function, API Gateway, S3
bucket, and IAM permissions.

**Files to Create:**

- `backend/template.yaml`

**Prerequisites:**

- Task 9 complete

**Implementation Steps:**

1. Create `backend/template.yaml` following the savorswipe template pattern:
   - `AWSTemplateFormatVersion: '2010-09-09'`
   - `Transform: AWS::Serverless-2016-10-31`
   - `Description: Omni Image - Chat-based image generation with Nova 2 Omni`
   - **Parameters:**
     - `StackName` (String, default `omni-image`, pattern `^[a-z][a-z0-9-]*$`)
     - `IncludeDevOrigins` (String, default `false`, allowed `true`/`false`)
     - `ProductionOrigins` (CommaDelimitedList, default `""`)
   - **Conditions:**
     - `IsDevMode` -- IncludeDevOrigins equals true
     - `HasProductionOrigins` -- first element of ProductionOrigins is not empty
   - **Resources:**
     - `ImageBucket` (S3 bucket):
       - Name: `${StackName}-images-${AWS::AccountId}`
       - Public access blocked
       - Lifecycle rule: delete rate-limit objects after 90 days
       - Tags: `Application: OmniImage`
     - `OmniImageFunction` (Serverless Function):
       - `FunctionName: ${StackName}-api`
       - `Handler: lambda_function.lambda_handler`
       - `Runtime: python3.11`
       - `CodeUri: .`
       - `MemorySize: 512`
       - `Timeout: 120`
       - Environment: `NOVA_IMAGE_BUCKET: !Ref ImageBucket`,
         `BEDROCK_REGION: us-west-2`, `ALLOWED_ORIGINS` (constructed from conditions)
       - Policies: S3 read/write on the bucket, Bedrock InvokeModel on the model
     - `HttpApi` (API Gateway v2 HTTP API):
       - CORS configuration matching the savorswipe pattern (dev vs production origins)
       - Routes: `POST /api/chat`, `GET /api/health`, `GET /api/usage`
     - `HttpApiStage` with throttling (burst 10, rate 100)
     - Lambda integration and permission
   - **Outputs:**
     - `ApiGatewayUrl`
     - `S3BucketName`
     - `FunctionName`
     - `FunctionArn`

**Verification Checklist:**

- [x] `sam validate --template backend/template.yaml` passes
- [x] Template parameters have sensible defaults
- [x] Lambda has minimal IAM permissions (S3 + Bedrock only)
- [x] CORS is configurable via parameters
- [x] API Gateway routes match FastAPI routes

**Testing Instructions:**

No automated tests for SAM templates. Manual verification:

- Run `sam validate --template backend/template.yaml`
- Verify template structure matches expected resources

**Commit Message Template:**

```text
feat(deploy): add SAM template for Lambda, API Gateway, and S3

- Define Lambda function with Python 3.11 runtime
- Configure API Gateway v2 with CORS and throttling
- Create S3 bucket for rate limiting and image storage
- Add IAM policies for Bedrock and S3 access
```

---

### Task 11: Deploy Script

**Goal:** Create the interactive deployment script that prompts for configuration, generates
`samconfig.toml`, runs SAM build and deploy, captures stack outputs, and writes the API
Gateway URL to the frontend `.env` file.

**Files to Create:**

- `scripts/deploy.js`

**Prerequisites:**

- Task 10 (SAM template) complete

**Implementation Steps:**

1. Create `scripts/deploy.js` following the savorswipe `deploy.js` pattern but simplified
   for omni-image (fewer parameters):
   - Constants: `PROJECT_ROOT`, `BACKEND_DIR`, `SAMCONFIG_PATH`, `ENV_PATH` (pointing
     to `frontend/.env`)
   - `loadEnvDeploy()` -- load existing config from `backend/.env.deploy` if it exists
   - `saveEnvDeploy(config)` -- save config for next deploy
   - Interactive prompts (using readline):
     - `Stack Name` (default: `omni-image`)
     - `AWS Region` (default: `us-west-2`)
     - `Include Dev Origins` (default: `true` -- since this is a demo app)
     - `Production Origins` (optional, comma-separated)
   - `generateSamConfig(config)` -- write `samconfig.toml` with stack name, region,
     S3 deploy bucket
   - Create SAM deployment bucket if needed (`aws s3 mb`)
   - Run `sam build` in backend directory
   - Run `sam deploy --parameter-overrides StackName=... IncludeDevOrigins=...
     ProductionOrigins=...`
   - `getStackOutputs(stackName, region)` -- query CloudFormation for outputs
   - `updateEnvFile(apiGatewayUrl)` -- write/update `PUBLIC_API_URL` in `frontend/.env`
   - Display deployment summary

1. Update root `package.json` to have the deploy script:
   `"deploy": "node scripts/deploy.js"`

**Verification Checklist:**

- [x] `node scripts/deploy.js --help` does not crash (the script can at least start)
- [x] `samconfig.toml` is generated with correct structure
- [x] Frontend `.env` is updated with API URL after deploy
- [x] Script handles missing `.env.deploy` gracefully (fresh deploy)

**Testing Instructions:**

No automated tests for the deploy script (it requires real AWS access). The script is
tested manually during first deployment.

**Commit Message Template:**

```text
feat(deploy): add interactive SAM deployment script

- Create scripts/deploy.js with interactive config prompts
- Generate samconfig.toml from user input
- Run sam build and sam deploy with parameter overrides
- Capture stack outputs and update frontend .env
- Add npm run deploy script to root package.json
```

---

### Task 12: CI Pipeline (Backend Only)

**Goal:** Create the GitHub Actions CI workflow with jobs for backend linting, type
checking, and testing. Frontend CI jobs are added later in Phase 2 Task 11 (after the
frontend directory exists) to avoid failures on a missing directory.

**Files to Create:**

- `.github/workflows/ci.yml`

**Prerequisites:**

- Tasks 1-9 complete (all backend code and tests exist)

**Implementation Steps:**

1. Create `.github/workflows/ci.yml` following the canvas-demo pattern:
   - Trigger on push to `main` and pull requests to `main`
   - `paths-ignore`: `docs/**`, `**/*.md`, `.claude/**`
   - Concurrency: cancel in-progress runs for same ref
   - **Jobs** (all run in parallel where possible):
     - `backend-lint`:
       - Setup Python 3.11, install uv
       - `uv pip install --system ruff`
       - `ruff check backend/src/ backend/tests/`
       - `ruff format --check backend/src/ backend/tests/`
     - `backend-typecheck`:
       - Setup Python 3.11, install uv
       - `cd backend && uv pip install --system -e .`
       - `cd backend && uv pip install --system mypy boto3-stubs[s3,bedrock-runtime]`
       - `cd backend && mypy src/`
     - `backend-test`:
       - Setup Python 3.11, install uv
       - `cd backend && uv pip install --system -e .`
       - `cd backend && uv pip install --system pytest pytest-cov httpx`
       - `cd backend && pytest tests/ -v --tb=short -m "not integration"`
       - `cd backend && pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=75 -m "not integration"`
     - `commit-lint`:
       - Only on pull requests
       - Check conventional commits format
     - `all-checks`:
       - Depends on all backend jobs and commit-lint
       - `if: always()`
       - Fails if any job failed

   Note: Frontend jobs (`frontend-lint`, `frontend-check`, `frontend-test`) are NOT
   included in this task. They are added in Phase 2 Task 11 after the `frontend/`
   directory exists. Including them here would cause CI failures on every push between
   Phase 1 completion and Phase 2 Task 1 completion.

   Note: The `backend-typecheck` job runs `cd backend && mypy src/` (not
   `mypy backend/src/` from the repo root). This ensures mypy discovers the
   `[tool.mypy]` config section in `backend/pyproject.toml`. All backend CI commands
   use `cd backend &&` consistently.

**Verification Checklist:**

- [x] CI YAML is valid (no syntax errors)
- [x] Backend jobs use Python 3.11 and uv
- [x] All backend commands use `cd backend &&` prefix for correct working directory
- [x] mypy runs from within `backend/` directory to pick up pyproject.toml config
- [x] Jobs run in parallel where possible
- [x] Paths-ignore excludes docs and markdown
- [x] No frontend jobs are present (those come in Phase 2 Task 11)

**Testing Instructions:**

No automated tests for CI config. Verify by pushing to a branch and checking GitHub Actions.

**Commit Message Template:**

```text
ci: add GitHub Actions workflow for backend checks

- Add parallel jobs for ruff lint, mypy typecheck, and pytest
- Add commit lint check on pull requests
- Add all-checks gate job
- Frontend CI jobs deferred to Phase 2
```

---

### Task 13: Backend .env.example and Documentation

**Goal:** Create the backend `.env.example` file for local development reference.

**Files to Create:**

- `backend/.env.example`

**Prerequisites:**

- Task 4 (config) complete

**Implementation Steps:**

1. Create `backend/.env.example` with all environment variables and comments:

   ```text
   # S3 bucket for rate limiting and image storage (required)
   NOVA_IMAGE_BUCKET=your-bucket-name

   # AWS region for the Lambda function
   AWS_REGION=us-west-2

   # Bedrock API region (Nova 2 Omni is in us-west-2 preview)
   BEDROCK_REGION=us-west-2

   # Rate limiting
   RATE_LIMIT=10
   RATE_LIMIT_WINDOW=3600

   # Logging
   LOG_LEVEL=INFO

   # CORS origins (comma-separated, * for all)
   ALLOWED_ORIGINS=*
   ```

**Verification Checklist:**

- [x] `.env.example` lists all environment variables from `AppConfig`
- [x] Comments explain each variable
- [x] No actual secrets in the file

**Testing Instructions:**

No tests needed -- this is a reference file.

**Commit Message Template:**

```text
docs(backend): add .env.example with all configuration variables

- Document all environment variables with descriptions
- Provide sensible defaults for local development
```

## Phase Verification

After completing all tasks in Phase 1:

1. **Run the full backend test suite:**

   ```bash
   cd backend
   uv run pytest tests/ -v --cov=src --cov-report=term-missing
   ```

   All tests must pass. Coverage must be >= 75%.

1. **Run linting and type checking:**

   ```bash
   cd backend
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   uv run mypy src/
   ```

   Zero errors on all commands.

1. **Validate SAM template:**

   ```bash
   sam validate --template backend/template.yaml
   ```

1. **Verify project structure matches:**

   ```text
   omni-image/
     .github/workflows/ci.yml
     .gitignore
     package.json
     scripts/deploy.js
     backend/
       .env.example
       lambda_function.py
       pyproject.toml
       template.yaml
       src/
         __init__.py
         app.py
         handlers/__init__.py
         handlers/chat.py
         handlers/health.py
         models/__init__.py
         models/config.py
         models/schemas.py
         services/__init__.py
         services/aws_client.py
         services/bedrock_service.py
         services/rate_limiter.py
         utils/__init__.py
         utils/exceptions.py
         utils/logger.py
       tests/
         __init__.py
         conftest.py
         test_aws_client.py
         test_bedrock_service.py
         test_config.py
         test_exceptions.py
         test_handlers.py
         test_lambda_function.py
         test_logger.py
         test_rate_limiter.py
         test_schemas.py
   ```

## Known Limitations

- **No integration tests with real AWS** -- all tests mock AWS services. First real
  validation happens at deploy time.
- **Nova 2 Omni is in preview** -- exact API parameter constraints (valid ranges for
  temperature, topP, topK, maxTokens) are not fully documented. The schema allows any
  values; the model may reject invalid ones at runtime.
- **Image dimension constraints unknown** -- may need to add validation after testing
  against the live API.
