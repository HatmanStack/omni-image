# Feature: Omni Image — Chat-based Image Generation with Nova 2 Omni

## Overview

A new application replacing the tab-based AWS Nova Canvas demo with a modern chat-based interface powered by Amazon Nova 2 Omni. Users interact through natural language — typing prompts and optionally uploading images — to generate and edit images via a conversational flow. The app displays generated images prominently with model text as captions.

The architecture is a monorepo with a SvelteKit static frontend deployed on AWS Amplify and a single Python Lambda function behind API Gateway that proxies Bedrock Converse API calls. The Lambda also handles S3 storage (inputs and outputs) and S3-backed rate limiting. This replaces the current containerized Gradio + Lambda deployment with a lighter, more maintainable stack.

The existing canvas-demo repo stays live as-is — it backs a published blog post and portfolio entry. Nova Canvas is not being deprecated. This new app is a separate portfolio piece showcasing the next-generation Omni model.

## Decisions

1. **New repo, not a migration** — canvas-demo stays live; omni-image is a fresh codebase at `~/projects/omni-image`
2. **Frontend framework: SvelteKit** — consistent with existing portfolio site (sv-portfolio), already known
3. **Backend: single Lambda + API Gateway** — no Docker/container, Mangum adapter for the Lambda handler
4. **UI paradigm: chat-based** — single conversational interface replaces 7-tab layout; images displayed prominently with text as captions below
5. **Example prompts** — starter suggestions shown to guide users (e.g., "Generate a sunset over mountains", "Remove the background from this image")
6. **Settings: API-mapped only** — only expose controls that correspond to real Nova 2 Omni Converse API parameters (inferenceConfig: maxTokens, temperature, topP, topK)
7. **Rate limiting: S3-backed, 10 req / 60 min** — carried over from canvas-demo pattern, tightened from 20/20min
8. **S3 storage: inputs and outputs** — store both user-uploaded images and model-generated images/text for monitoring
9. **Content moderation: Bedrock guardrails only** — drop external HuggingFace NSFW check, rely on Omni's built-in filtering
10. **Auth: fully public** — no API keys, no Cognito; rate limiter is the abuse protection
11. **Monorepo structure** — `/frontend` (SvelteKit) and `/backend` (Lambda Python)
12. **CI: full pipeline** — ruff, mypy, pytest for backend; lint + build for frontend via GitHub Actions
13. **Deployment: Amplify** — user handles Amplify deploy manually, default Amplify URL
14. **No mock layer** — build against real Omni API (`us.amazon.nova-2-omni-v1:0`), no stubs
15. **Model: Nova 2 Omni** — model ID `us.amazon.nova-2-omni-v1:0`, Converse API, region us-west-2

## Scope: In

- SvelteKit chat UI with text input, image upload, and message history
- Image display with text captions in chat bubbles
- Example prompt suggestions for new users
- Collapsible settings panel with real Omni API parameters
- Single Lambda function: receives chat messages, calls Bedrock Converse API, stores to S3, returns response
- API Gateway routing to Lambda
- S3-backed rate limiter (10 req / 60 min)
- S3 storage of input images, output images, and response text
- CI pipeline: ruff, mypy, pytest (backend); svelte-check, eslint (frontend)
- Monorepo with `/frontend` and `/backend` directories
- Python backend with uv for package management
- `npm run deploy` script for backend deployment (SAM build + deploy, interactive config prompts, stack output capture)

## Scope: Out

- Docker/container deployment
- Gradio UI
- Nova Canvas support or backward compatibility
- Custom domain
- User authentication (Cognito, API keys)
- External NSFW checking (HuggingFace)
- Mock/stub Bedrock layer
- Amplify deployment automation (user handles manually)
- Multi-turn conversation memory on the backend (stateless Lambda; conversation state lives in the frontend)

## Open Questions

- **Omni API parameter constraints** — exact valid ranges for temperature, topP, topK, maxTokens when generating images are not fully documented yet (model is in preview). Will need to verify once access is available.
- **Image dimension constraints** — unclear if Omni has the same 256-2048px / multiples of 64 / 4:1 ratio limits as Canvas. May need to discover empirically.
- **Omni image editing via Converse API** — the exact mechanism for sending images for editing (as message content blocks) and instructing edits via natural language needs validation against the live API. Documentation shows it's message-based but specific patterns (e.g., mask handling) are not well documented.
- **Region availability** — preview is us-west-2; may change at GA.

## Relevant Codebase Context

### From canvas-demo (patterns to carry over)
- `src/services/rate_limiter.py` — S3-backed rate limiter with ETag optimistic locking, adapt for 10/60min window
- `src/services/aws_client.py` — Thread-safe singleton AWS client manager with connection pooling; adapt for Converse API
- `src/models/config.py` — Dataclass-based config reading from env vars (`AMP_AWS_ID`/`AMP_AWS_SECRET`)
- `src/utils/exceptions.py` — Custom exception hierarchy (CanvasError, ImageError, RateLimitError, etc.)
- `src/utils/logger.py` — CloudWatch log batching for Lambda environments
- `.github/workflows/ci.yml` — CI pipeline structure (lint, type check, test as parallel jobs)

### New patterns needed
- Mangum adapter for FastAPI/Lambda integration
- SvelteKit project structure with API client
- API Gateway configuration (or Lambda Function URL)
- Converse API request/response handling (message-based, not task-type-based)
- Frontend state management for chat history and image display

### Reference repos
- `~/projects/canvas-demo` — the existing Nova Canvas app; use as the primary reference for backend patterns (rate limiter, AWS client, config, exceptions, logging, CI pipeline, Lambda deployment, image processing). The new backend should follow the same conventions and quality bar.
- `~/projects/sv-portfolio` — the user's SvelteKit portfolio site; reference for SvelteKit patterns and conventions the user is familiar with
- `~/projects/savorswipe` — reference for the deployment pattern. Has an `npm run deploy` script (`frontend/scripts/deploy.js`) that interactively prompts for config (region, API keys), generates `samconfig.toml`, runs `sam build && sam deploy`, captures stack outputs, and updates `.env`. The new omni-image app should have a similar `npm run deploy` experience for the backend Lambda + API Gateway stack.

## Nova 2 Omni API Research Summary

### Model Details
- **Model ID**: `us.amazon.nova-2-omni-v1:0`
- **Region**: us-west-2 (preview)
- **Status**: Public preview (Nova Forge customers), announced re:Invent December 2025
- **API**: Converse API (`client.converse()`) or Invoke API (`client.invoke_model()`) via `bedrock-runtime`

### Converse API Request Structure
Messages-based format — no task types, no structured params like Canvas. All operations (generation, editing, background removal, etc.) are expressed as natural language in message content blocks:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        { "text": "Remove the background from this image" },
        {
          "image": {
            "format": "jpeg | png | gif | webp",
            "source": {
              "bytes": "<binary array (Converse) or base64 string (Invoke)>"
            }
          }
        }
      ]
    }
  ],
  "inferenceConfig": {
    "maxTokens": int,
    "temperature": float,
    "topP": float,
    "topK": int,
    "stopSequences": ["string"]
  }
}
```

### Converse API Response Structure
Responses can contain both text and images in the same message:

```json
{
  "output": {
    "message": {
      "role": "assistant",
      "content": [
        { "text": "description text" },
        {
          "image": {
            "format": "png",
            "source": {
              "bytes": "<binary array (Converse) or base64 string (Invoke)>"
            }
          }
        }
      ]
    }
  },
  "stopReason": "end_turn",
  "usage": { "inputTokens": int, "outputTokens": int, "totalTokens": int },
  "metrics": { "latencyMs": int }
}
```

### Key Differences from Nova Canvas API
| Aspect | Nova Canvas | Nova 2 Omni |
|--------|-------------|-------------|
| API call | `invoke_model()` with task-type JSON | `converse()` with message content blocks |
| Operations | Explicit `taskType` enum: `TEXT_IMAGE`, `INPAINTING`, `OUTPAINTING`, `IMAGE_VARIATION`, `COLOR_GUIDED_GENERATION`, `BACKGROUND_REMOVAL` | Natural language — all operations via prompt text |
| Image config | `imageGenerationConfig`: `seed`, `cfgScale`, `quality`, `height`, `width`, `numberOfImages` | `inferenceConfig`: `maxTokens`, `temperature`, `topP`, `topK` |
| Masks | Structured `maskImage` (base64) and `maskPrompt` fields | Send image + natural language edit instructions |
| Output format | JSON with `images[]` base64 array | Message `content[]` with `image` and `text` objects |
| Output image format | Configurable | Always PNG |

### Image Editing Capabilities (9 operations via natural language)
1. Adding new objects
2. Altering objects
3. Extracting info about objects
4. Replacing objects
5. Removing objects
6. Background changes
7. Style transfer (new — not in Canvas)
8. Text rendering within images (new — not in Canvas)
9. Character consistency (new — not in Canvas)

### Reference Documentation
- AWS Nova 2 User Guide: https://docs.aws.amazon.com/nova/latest/nova2-userguide/
- Nova 2 Request/Response Schema: https://docs.aws.amazon.com/nova/latest/nova2-userguide/request-response-schema.html
- Nova 2 PDF Developer Guide: https://docs.aws.amazon.com/pdfs/nova/latest/nova2-userguide/nova2-ug.pdf
- Bedrock Supported Models: https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
- Bedrock Model Lifecycle: https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html
- AWS Samples Repo (workshops/notebooks): https://github.com/aws-samples/sample-building-intelligent-multimodal-applications-with-Nova
- re:Invent 2025 Nova 2 Omni Session: https://dev.to/kazuya_dev/aws-reinvent-2025-new-launch-amazon-nova-2-omni-a-new-frontier-in-multimodal-ai-aim3324-1bnp
- Nova 2 Omni Preview Announcement: https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-nova-2-omni-preview/
- Amazon Science Technical Report: https://www.amazon.science/publications/amazon-nova-2-multimodal-reasoning-and-generation-models

### Nova Canvas Lifecycle Note
Nova Canvas (`amazon.nova-canvas-v1:0`) is **not** on AWS's deprecation/EOL list as of April 2026. Only Nova Premier and Nova Sonic v1 are scheduled for EOL (September 14, 2026). Canvas continues to be supported.

## Technical Constraints

- **Python >=3.11** for backend (consistent with canvas-demo)
- **Nova 2 Omni is in preview** — requires Nova Forge customer access; model ID `us.amazon.nova-2-omni-v1:0` in us-west-2
- **Converse API** — replaces InvokeModel; request/response uses message content blocks with text and image objects
- **Image output is always PNG** from Omni
- **uv** for Python package management (not pip)
- **S3 required** for rate limiting and image storage
- **Lambda cold start** — single Lambda should stay lightweight; no heavy dependencies beyond boto3
