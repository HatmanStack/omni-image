# Phase 0 -- Foundation

This phase establishes architecture decisions, conventions, and patterns that apply to all
subsequent phases. No code is written here -- this is the reference document for the
implementation engineer.

## Architecture Decisions

### ADR-1: Monorepo Structure

The project uses a monorepo with `/frontend` (SvelteKit) and `/backend` (Python Lambda)
directories. A root `package.json` provides workspace-level scripts (e.g., `npm run deploy`
for backend deployment). This matches the savorswipe pattern.

```text
omni-image/
  frontend/           # SvelteKit static site
    src/
    static/
    package.json
    svelte.config.js
    vite.config.ts
    amplify.yml
  backend/            # Python Lambda + SAM
    src/
      handlers/
      models/
      services/
      utils/
    tests/
    template.yaml
    pyproject.toml
  package.json        # Root workspace scripts (deploy, etc.)
  .github/
    workflows/
      ci.yml
```

### ADR-2: Backend Framework -- FastAPI + Mangum

The Lambda function uses FastAPI as the web framework with Mangum as the Lambda adapter.
FastAPI provides automatic request validation, OpenAPI docs, and a clean routing layer.
Mangum translates API Gateway events into ASGI requests for FastAPI.

- **FastAPI** handles routing, request/response models, CORS middleware
- **Mangum** wraps the FastAPI app as a Lambda handler
- The Lambda handler file (`lambda_function.py`) is minimal -- it imports the FastAPI app
  and wraps it with Mangum

### ADR-3: Converse API (Not InvokeModel)

Nova 2 Omni uses the Bedrock Converse API (`client.converse()`), not `invoke_model()`.
All operations (generation, editing, background removal, etc.) are expressed as natural
language in message content blocks. The backend receives the full conversation history from
the frontend and forwards it to the Converse API.

### ADR-4: Stateless Lambda -- Frontend Owns Conversation State

The Lambda is stateless. Conversation history lives entirely in the frontend. Each API
request includes the full message history needed for the current turn. The backend does
not persist or reconstruct conversation context.

### ADR-5: S3-backed Rate Limiting (10 req / 60 min)

Carried over from canvas-demo but simplified. No premium/standard tiers -- all requests
cost 1. Window is 60 minutes, limit is 10 requests. Same optimistic locking pattern with
ETag-based concurrency control. Fail-open on errors.

### ADR-6: No Auth -- Rate Limiter is Abuse Protection

Fully public API. No API keys, no Cognito. Rate limiting plus API Gateway throttling
provide basic abuse protection. Same philosophy as savorswipe.

### ADR-7: SAM Deployment with Interactive Deploy Script

Backend deploys via AWS SAM (`sam build && sam deploy`). An `npm run deploy` script in the
root `package.json` runs an interactive Node.js script (following the savorswipe pattern)
that prompts for configuration, generates `samconfig.toml`, runs SAM, captures stack
outputs, and writes the API Gateway URL to the frontend `.env` file.

### ADR-8: Amplify Frontend Deployment (Manual)

The SvelteKit frontend is deployed manually to AWS Amplify. The `amplify.yml` build spec
uses pnpm. The user connects the repo to Amplify through the AWS console. No automation
for this step.

## Tech Stack

### Backend

| Component | Choice | Version |
|-----------|--------|---------|
| Language | Python | >= 3.11 |
| Package manager | uv | latest |
| Web framework | FastAPI | >= 0.115 |
| Lambda adapter | Mangum | >= 0.19 |
| AWS SDK | boto3 | >= 1.35 |
| Linter | ruff | >= 0.4 |
| Type checker | mypy (strict) | >= 1.10 |
| Test framework | pytest | >= 8.0 |
| Coverage | pytest-cov | >= 4.0 |

### Frontend

| Component | Choice | Version |
|-----------|--------|---------|
| Framework | SvelteKit | latest (Svelte 5) |
| Package manager | pnpm | latest |
| Adapter | @sveltejs/adapter-static | latest |
| Linter | eslint + eslint-plugin-svelte | latest |
| Type checker | svelte-check | latest |
| Test framework | vitest + @testing-library/svelte | latest |
| Formatter | prettier + prettier-plugin-svelte | latest |

### Infrastructure

| Component | Choice |
|-----------|--------|
| Compute | AWS Lambda (Python 3.11 runtime) |
| API | API Gateway v2 (HTTP API) |
| Storage | S3 (rate limiting + image/response storage) |
| Frontend hosting | AWS Amplify |
| IaC | AWS SAM (template.yaml) |
| CI | GitHub Actions |

## Testing Strategy

### Backend Testing

All tests run without real AWS credentials. Tests use `unittest.mock` to mock boto3 clients.

- **conftest.py** sets environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `NOVA_IMAGE_BUCKET`, etc.) before any imports, following the canvas-demo pattern
- **Config singleton** is reset between tests via `reset_config()` fixture (autouse)
- **AWS client singleton** is reset between tests via `AWSClientManager._reset()`
- **Bedrock responses** are mocked with fixtures that return realistic Converse API
  response structures (content blocks with text and image objects)
- **S3 operations** are mocked at the boto3 client level
- **FastAPI endpoints** are tested via `httpx.AsyncClient` with the FastAPI test client

Test markers:

- `@pytest.mark.unit` -- unit tests (no external dependencies)
- `@pytest.mark.integration` -- integration tests (mocked AWS, but test full request flow)

### Frontend Testing

- Component tests use `@testing-library/svelte` with `vitest` and `jsdom`
- API calls are mocked using `vi.mock` or `msw` (Mock Service Worker)
- No real backend calls in any test

### CI Pipeline

GitHub Actions with parallel jobs:

1. **backend-lint** -- `ruff check` + `ruff format --check`
1. **backend-typecheck** -- `mypy src/`
1. **backend-test** -- `pytest` with coverage (fail under 75%)
1. **frontend-lint** -- `eslint` + `prettier --check`
1. **frontend-check** -- `svelte-check`
1. **frontend-test** -- `vitest run`
1. **commit-lint** -- conventional commits check on PRs

## Shared Patterns and Conventions

### Backend Patterns (Carried from canvas-demo)

- **Singleton pattern** for AWS clients and services (module-level `_instance` with
  `get_X()` / `reset_X()` functions)
- **Dataclass config** reading from environment variables with validation
- **Custom exception hierarchy** rooted in a base `OmniImageError`
- **CloudWatch logger** with batch flushing in Lambda environments
- **`log_performance` decorator** for timing critical operations
- **Async S3 storage** via thread pool executor (fire-and-forget for response archival)

### Frontend Patterns (From sv-portfolio)

- **SvelteKit static adapter** with `adapter-static`
- **TypeScript** throughout
- **Svelte 5 runes** (`$state`, `$derived`, `$effect`) for reactivity
- **Component tests** co-located with components (e.g., `Component.test.ts` next to
  `Component.svelte`)

### Commit Message Format

Conventional commits:

```text
type(scope): brief description

- Detail 1
- Detail 2
```

Valid types: `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`, `style`, `build`

Scopes: `backend`, `frontend`, `ci`, `deploy`, `root`

## Environment Variables

### Backend (Lambda)

| Variable | Description | Required |
|----------|-------------|----------|
| `NOVA_IMAGE_BUCKET` | S3 bucket for rate limiting and storage | Yes |
| `AWS_REGION` | AWS region for the Lambda | Yes (set by Lambda runtime) |
| `BEDROCK_REGION` | Region for Bedrock API calls | No (default: `us-west-2`) |
| `RATE_LIMIT` | Max requests per window | No (default: `10`) |
| `RATE_LIMIT_WINDOW` | Window size in seconds | No (default: `3600`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | No (default: `*`) |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `PUBLIC_API_URL` | API Gateway URL for the backend | Yes |
