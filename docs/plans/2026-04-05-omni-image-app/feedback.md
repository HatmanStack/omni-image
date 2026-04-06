# Feedback -- Omni Image Implementation Plan

## Active Feedback

<!-- Feedback items are added here by Plan Reviewer and Code Reviewer -->
<!-- Format: -->
<!-- ### FB-001: [Title] -->
<!-- - **Source:** PLAN_REVIEW | CODE_REVIEW -->
<!-- - **Phase:** Phase-N -->
<!-- - **Task:** Task N (if applicable) -->
<!-- - **Severity:** BLOCKING | MAJOR | MINOR -->
<!-- - **Description:** Details of the issue -->
<!-- - **Suggested Resolution:** How to fix it -->

### FB-005: CRITICAL -- Frontend-backend image block format mismatch breaks image upload

- **Source:** FINAL_REVIEW
- **Phase:** Phase-2
- **Task:** Task 3 (Chat Store) / Phase-1 Task 9 (Schemas)
- **Severity:** BLOCKING
- **Category:** Implementation-level (Implementer)
- **Description:** The frontend `chatMessagesToApiMessages()` in `frontend/src/lib/stores/chat.svelte.ts` sends image content blocks as `{ type: 'image', format: 'png', data: 'base64...' }`. However, the backend Pydantic schema `ImageBlock` in `backend/src/models/schemas.py` expects `{ image: { format: 'png', data: 'base64...' } }`. When a user uploads an image, the backend returns a 422 validation error because the frontend's image block format does not match either `TextBlock` (no `text` field) or `ImageBlock` (no `image` field). Verified by running `Message.model_validate()` against the frontend's format -- it fails with "Field required" for both union variants.
- **Suggested Resolution:** Either (a) change the frontend `chatMessagesToApiMessages` to emit `{ image: { format, data } }` instead of `{ type: 'image', format, data }`, or (b) add a Pydantic discriminator and restructure the backend schemas. Option (a) is the minimal fix. The frontend TextBlock format `{ type: 'text', text: '...' }` works because Pydantic matches on the `text` field (ignoring extra fields), so only the image path is broken.

### FB-006: S3 request archival fails silently for image-containing requests

- **Source:** FINAL_REVIEW
- **Phase:** Phase-1
- **Task:** Task 6 (Bedrock Converse Service)
- **Severity:** MAJOR
- **Category:** Implementation-level (Implementer)
- **Description:** In `backend/src/services/bedrock_service.py`, `_store_response_sync()` calls `json.dumps(messages)` to serialize the request for S3 archival. However, `messages` contains raw `bytes` objects (from decoded base64 image data in the chat handler's `_convert_messages`). `bytes` is not JSON serializable, so `json.dumps()` raises `TypeError`. The `except Exception` block catches this and logs a warning, so it does not crash the request, but all image-containing requests will fail to archive to S3. This means the monitoring/archival feature is non-functional for the primary use case (image generation).
- **Suggested Resolution:** Either (a) base64-encode the image bytes before serializing (e.g., replace bytes with a base64 string in the stored JSON), or (b) store the request as a separate format that handles binary data, or (c) strip image bytes from the archived request and store only metadata.

## Resolved Feedback

### FB-001: CI frontend jobs will fail after Phase 1

- **Resolution:** Split CI into two stages. Phase 1 Task 12 now creates the CI workflow
  with backend-only jobs (backend-lint, backend-typecheck, backend-test, commit-lint).
  A new Phase 2 Task 11 adds the frontend jobs (frontend-lint, frontend-check,
  frontend-test) to the existing workflow after the frontend directory exists. The
  all-checks gate job is updated in Phase 2 Task 11 to include the new frontend jobs.
- **Resolved By:** PLAN_AUTHOR

### FB-002: Phase-2 Task 9 styling modifications are ambiguous

- **Resolution:** Scoped Task 9 to only creating `app.css` and updating `+layout.svelte`
  to import it. The task explicitly states that no component files are modified. Components
  keep their existing scoped styles from Tasks 4-8. CSS custom properties are defined on
  `:root` and cascade to all components, but referencing them is optional and not part of
  this task. The "Files to Modify" section now lists only `+layout.svelte` with the
  specific change (add import). The ambiguous "Review and refine component styles"
  instruction has been removed.
- **Resolved By:** PLAN_AUTHOR

### FB-003: Phase-1 Task 12 CI mypy working directory is unclear

- **Resolution:** Changed the mypy command from `mypy backend/src/` (running from repo
  root) to `cd backend && mypy src/` (running from within the backend directory). This
  ensures mypy discovers the `[tool.mypy]` config section in `backend/pyproject.toml`.
  Also changed the uv pip install commands in the same job to use `cd backend &&` prefix
  consistently. Added an explicit note in the implementation steps explaining why all
  backend CI commands use `cd backend &&`.
- **Resolved By:** PLAN_AUTHOR

### FB-004: Phase-2 Task 8 test file naming may confuse implementer

- **Resolution:** Added a parenthetical note to the testing instructions in Phase 2 Task 8
  explaining that test files do NOT use the `+` prefix because they are not SvelteKit route
  modules. Only files that SvelteKit processes as routes use the `+` prefix
  (`+page.svelte`, `+layout.svelte`, etc.); test files are plain TypeScript picked up by
  vitest.
- **Resolved By:** PLAN_AUTHOR
