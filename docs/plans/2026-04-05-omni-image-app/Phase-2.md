# Phase 2 -- Frontend Implementation

## Phase Goal

Build the complete SvelteKit frontend: a chat-based interface where users type prompts and
optionally upload images to generate and edit images via Nova 2 Omni. The UI displays
generated images prominently in chat bubbles with model text as captions. Includes example
prompt suggestions, a collapsible settings panel, and Amplify deployment configuration.

**Success criteria:**

- All frontend tests pass
- `svelte-check` passes with zero errors
- `eslint` passes with zero errors
- `prettier --check` passes
- `pnpm build` produces a static site without errors
- Chat UI sends messages to the backend and displays responses

**Estimated tokens:** ~40,000

## Prerequisites

- Phase 0 and Phase 1 complete
- Backend deployed (API Gateway URL available) OR `PUBLIC_API_URL` set in `frontend/.env`
  for local development against a deployed backend
- Node.js >= 20 and pnpm installed

## Tasks

### Task 1: Frontend Project Scaffolding

**Goal:** Create the SvelteKit project with static adapter, TypeScript, linting, testing,
and Amplify build configuration.

**Files to Create:**

- `frontend/package.json` -- Project config with scripts and dependencies
- `frontend/svelte.config.js` -- SvelteKit config with static adapter
- `frontend/vite.config.ts` -- Vite config with vitest
- `frontend/vitest.config.ts` -- Vitest config for component tests
- `frontend/tsconfig.json` -- TypeScript config
- `frontend/eslint.config.js` -- ESLint config with Svelte plugin
- `frontend/.prettierrc` -- Prettier config
- `frontend/.prettierignore` -- Prettier ignore
- `frontend/amplify.yml` -- Amplify build spec
- `frontend/src/app.html` -- HTML shell
- `frontend/src/app.d.ts` -- SvelteKit type declarations
- `frontend/static/favicon.png` -- Placeholder favicon (1x1 transparent PNG is fine)

**Implementation Steps:**

1. Initialize the SvelteKit project. The fastest approach is to create the files manually
   (do not run `npx sv create` -- set up files directly to match our exact config).

1. Create `frontend/package.json`:
   - `name`: `omni-image-frontend`
   - `type`: `module`
   - Scripts: `dev`, `build`, `preview`, `check`, `test`, `lint`, `format`, `format:check`
   - Dependencies: none (SvelteKit is all devDeps for static sites)
   - DevDependencies:
     - `@sveltejs/adapter-static`, `@sveltejs/kit`, `@sveltejs/vite-plugin-svelte`
     - `svelte`, `svelte-check`, `typescript`
     - `vite`, `vitest`, `@vitest/coverage-v8`
     - `@testing-library/svelte`, `@testing-library/jest-dom`, `jsdom`
     - `eslint`, `eslint-plugin-svelte`, `eslint-config-prettier`, `globals`
     - `prettier`, `prettier-plugin-svelte`
     - `typescript-eslint`

1. Create `frontend/svelte.config.js` following sv-portfolio pattern:
   - Use `adapter-static` with `pages: 'build'`, `assets: 'build'`,
     `fallback: '200.html'` (SPA fallback), `precompress: true`
   - Use `vitePreprocess()`

1. Create `frontend/vite.config.ts`:
   - Import `sveltekit` from `@sveltejs/kit/vite`
   - Export default with `plugins: [sveltekit()]`

1. Create `frontend/vitest.config.ts`:
   - Extend from vite config
   - Set `test.environment: 'jsdom'`
   - Set `test.include: ['src/**/*.test.ts']`
   - Set `test.globals: true`

1. Create `frontend/tsconfig.json` with SvelteKit defaults

1. Create `frontend/eslint.config.js` following sv-portfolio pattern

1. Create `frontend/.prettierrc`:
   `{"useTabs": true, "singleQuote": true, "trailingComma": "none", "plugins": ["prettier-plugin-svelte"]}`

1. Create `frontend/amplify.yml` following sv-portfolio pattern:
   - preBuild: `corepack enable && pnpm install`
   - build: `pnpm build`
   - artifacts: `baseDirectory: build`, `files: '**/*'`

1. Create `frontend/src/app.html`:
   - Standard SvelteKit HTML shell with `%sveltekit.head%` and `%sveltekit.body%`
   - Include viewport meta tag
   - Set page title: "Omni Image"

1. Create `frontend/src/app.d.ts` with SvelteKit ambient types

**Verification Checklist:**

- [x] `cd frontend && pnpm install` succeeds
- [x] `cd frontend && pnpm run check` passes
- [x] `cd frontend && pnpm run lint` passes
- [x] `cd frontend && pnpm run build` produces output in `frontend/build/`

**Testing Instructions:**

No tests yet -- this is scaffolding. Verify with the commands above.

**Commit Message Template:**

```text
chore(frontend): scaffold SvelteKit project with static adapter

- Create package.json with all dev dependencies
- Configure SvelteKit with adapter-static for Amplify
- Set up TypeScript, ESLint, Prettier, Vitest
- Add amplify.yml build spec
```

---

### Task 2: API Client and Types

**Goal:** Create the TypeScript API client that communicates with the backend, and define
the shared types for messages, requests, and responses.

**Files to Create:**

- `frontend/src/lib/types.ts` -- TypeScript interfaces and types
- `frontend/src/lib/api.ts` -- API client functions
- `frontend/src/lib/config.ts` -- Environment variable access

**Prerequisites:**

- Task 1 complete

**Implementation Steps:**

1. Create `frontend/src/lib/config.ts`:
   - Export `API_URL` from `import.meta.env.PUBLIC_API_URL` (SvelteKit public env var)
   - Throw error at build time if `PUBLIC_API_URL` is not set (use a fallback to
     `'http://localhost:8000'` for local development to avoid build failures)

1. Create `frontend/src/lib/types.ts`:
   - `ContentBlock` -- discriminated union: `TextBlock { type: 'text'; text: string }` or
     `ImageBlock { type: 'image'; format: string; data: string }` (data is base64)
   - `Message` -- `{ role: 'user' | 'assistant'; content: ContentBlock[] }`
   - `InferenceConfig` -- `{ maxTokens?: number; temperature?: number; topP?: number; topK?: number }`
   - `ChatRequest` -- `{ messages: Message[]; inferenceConfig?: InferenceConfig }`
   - `ChatResponse` -- `{ text: string | null; image: string | null; usage: Record<string, number> | null; latency_ms: number | null }`
   - `ErrorResponse` -- `{ error: string; error_code: string }`
   - `UsageResponse` -- `{ total_requests: number; limit: number; remaining: number }`
   - `ChatMessage` -- UI-level type: `{ id: string; role: 'user' | 'assistant'; text?: string; image?: string; imageFormat?: string; timestamp: Date; isLoading?: boolean }`

1. Create `frontend/src/lib/api.ts`:
   - `sendChat(request: ChatRequest): Promise<ChatResponse>` -- POST to `/api/chat`
     - Include `Content-Type: application/json` header
     - Parse response JSON
     - On non-2xx, parse `ErrorResponse` and throw an `Error` with the message
   - `getUsage(): Promise<UsageResponse>` -- GET `/api/usage`
   - `getHealth(): Promise<{ status: string; model: string; region: string }>` -- GET `/api/health`
   - All functions use `fetch()` with `API_URL` as base URL
   - All functions handle network errors with descriptive messages

**Verification Checklist:**

- [x] Types are importable from `$lib/types`
- [x] API client compiles without TypeScript errors
- [x] `svelte-check` passes

**Testing Instructions:**

Write `frontend/src/lib/api.test.ts`:

- Test `sendChat()` sends correct request body (mock `fetch`)
- Test `sendChat()` parses successful response
- Test `sendChat()` throws on error response (4xx, 5xx)
- Test `sendChat()` throws on network error
- Test `getUsage()` parses response
- Test `getHealth()` parses response

Use `vi.stubGlobal('fetch', vi.fn())` to mock fetch.

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add TypeScript types and API client

- Define message, request, and response types
- Create API client for chat, usage, and health endpoints
- Add config module for environment variable access
- Add unit tests for API client with mocked fetch
```

---

### Task 3: Chat Store (State Management)

**Goal:** Create a reactive Svelte store that manages chat message history, loading state,
settings, and API interactions.

**Files to Create:**

- `frontend/src/lib/stores/chat.svelte.ts` -- Chat state management using Svelte 5 runes

**Prerequisites:**

- Task 2 complete

**Implementation Steps:**

1. Create `frontend/src/lib/stores/chat.svelte.ts`:
   - Use Svelte 5 runes (`$state`, `$derived`) for reactive state
   - Export a `createChatStore()` function that returns an object with:
     - **State:**
       - `messages: ChatMessage[]` -- `$state([])`, the full chat history
       - `isLoading: boolean` -- `$state(false)`
       - `error: string | null` -- `$state(null)`
       - `settings: InferenceConfig` -- `$state({})` with default values
     - **Derived:**
       - `hasMessages: boolean` -- `$derived(() => messages.length > 0)`
       - `lastMessage: ChatMessage | undefined` -- `$derived`
     - **Actions:**
       - `sendMessage(text: string, imageFile?: File): Promise<void>`:
         1. Create a user `ChatMessage` with the text. If `imageFile` is provided,
            read it as base64 using `FileReader` and add an `ImageBlock` to the
            content.
         1. Append user message to `messages`
         1. Append a loading assistant message (with `isLoading: true`)
         1. Set `isLoading = true`, `error = null`
         1. Build the `ChatRequest` from the full `messages` array (convert
            `ChatMessage[]` to `Message[]` for the API -- text content becomes
            `TextBlock`, image becomes `ImageBlock`)
         1. Call `sendChat(request)`
         1. On success: replace the loading message with the real assistant message
            (text and/or image from response)
         1. On error: remove the loading message, set `error` to the error message.
            If it is a rate limit error (429), include a user-friendly message about
            the limit.
         1. Set `isLoading = false`
       - `clearMessages(): void` -- reset messages to empty array
       - `clearError(): void` -- set error to null
       - `updateSettings(config: Partial<InferenceConfig>): void`
   - Helper function `fileToBase64(file: File): Promise<string>` -- reads a File to
     base64 string using FileReader
   - Helper function `chatMessagesToApiMessages(messages: ChatMessage[]): Message[]` --
     converts UI messages to API format (exclude loading messages, convert image data
     to ImageBlock)

**Verification Checklist:**

- [x] Store is importable and creates reactive state
- [x] `sendMessage` appends user message and loading indicator
- [x] `sendMessage` replaces loading indicator with response
- [x] `sendMessage` handles errors and removes loading indicator
- [x] `clearMessages` resets state
- [x] Settings are passed through to API requests

**Testing Instructions:**

Write `frontend/src/lib/stores/chat.svelte.test.ts`:

- Test `sendMessage` with text only -- verify user message added, API called, assistant
  message added
- Test `sendMessage` with text and image file -- verify image is base64 encoded
- Test `sendMessage` error handling -- verify loading message removed, error set
- Test `clearMessages` resets messages array
- Test `updateSettings` updates inference config
- Test `chatMessagesToApiMessages` conversion (exclude loading messages)
- Mock `sendChat` from `$lib/api`

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add reactive chat store with Svelte 5 runes

- Create chat state management with messages, loading, and error
- Implement sendMessage with user/assistant message flow
- Add file-to-base64 conversion for image uploads
- Add settings management for inference config
- Add unit tests for store actions and state transitions
```

---

### Task 4: Chat Message Component

**Goal:** Create the chat message component that displays user and assistant messages,
including text and images.

**Files to Create:**

- `frontend/src/lib/components/ChatMessage.svelte`
- `frontend/src/lib/components/ChatMessage.test.ts`

**Prerequisites:**

- Task 2 complete (types defined)

**Implementation Steps:**

1. Create `frontend/src/lib/components/ChatMessage.svelte`:
   - Accept a `message: ChatMessage` prop
   - Render differently based on `message.role`:
     - **User messages:** right-aligned bubble with user's text. If image is present,
       display a thumbnail of the uploaded image above the text.
     - **Assistant messages:** left-aligned bubble. If image is present, display the
       generated image prominently (large, taking most of the bubble width). If text
       is present, display it as a caption below the image. If only text, display it
       as a regular message.
     - **Loading state:** if `message.isLoading`, show a loading indicator (animated
       dots or spinner) in the assistant bubble
   - Images are displayed as `<img>` tags with `src="data:image/png;base64,{data}"`
   - Include CSS/styles directly in the component (scoped)
   - Use semantic HTML (`<article>`, `<p>`, `<figure>` for images)
   - Add `aria-label` attributes for accessibility

**Verification Checklist:**

- [x] User messages render right-aligned with text
- [x] User messages with images show the image
- [x] Assistant messages with images show image prominently with text caption
- [x] Assistant text-only messages render as regular bubbles
- [x] Loading state shows indicator
- [x] Component passes `svelte-check`

**Testing Instructions:**

Write `frontend/src/lib/components/ChatMessage.test.ts`:

- Test user text message renders with correct text
- Test user message with image renders `<img>` tag
- Test assistant text message renders with correct text
- Test assistant image+text message renders image and caption
- Test loading message renders loading indicator
- Use `@testing-library/svelte` `render` function

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add ChatMessage component with image display

- Create chat bubble component for user and assistant messages
- Display generated images prominently with text captions
- Add loading state indicator
- Add scoped CSS for message styling
- Add component tests for all message types
```

---

### Task 5: Chat Input Component

**Goal:** Create the chat input component with a text field, image upload button, and send
button.

**Files to Create:**

- `frontend/src/lib/components/ChatInput.svelte`
- `frontend/src/lib/components/ChatInput.test.ts`

**Prerequisites:**

- Task 2 complete (types defined)

**Implementation Steps:**

1. Create `frontend/src/lib/components/ChatInput.svelte`:
   - **Text input:** a `<textarea>` that auto-resizes, with placeholder text
     "Describe an image to generate, or upload an image to edit..."
   - **Image upload button:** a button with an image/paperclip icon that triggers a
     hidden `<input type="file" accept="image/*">`. When a file is selected, show a
     small preview thumbnail above the input area with an "X" button to remove it.
   - **Send button:** disabled when no text and no image, or when `isLoading` is true
   - **Keyboard shortcut:** Enter sends (Shift+Enter for newline)
   - **Props:**
     - `onSend: (text: string, imageFile?: File) => void` -- callback when user sends
     - `isLoading: boolean` -- disables input when true
   - **State (local):**
     - `text: string` -- current input text
     - `imageFile: File | null` -- selected image file
     - `imagePreview: string | null` -- data URL for preview thumbnail
   - On send: call `onSend`, clear text and image, reset textarea height

**Verification Checklist:**

- [x] Text input accepts and displays typed text
- [x] Enter key sends, Shift+Enter adds newline
- [x] Image upload shows preview thumbnail
- [x] "X" button removes selected image
- [x] Send button disabled when empty and when loading
- [x] Input clears after sending

**Testing Instructions:**

Write `frontend/src/lib/components/ChatInput.test.ts`:

- Test typing text updates the textarea
- Test send button click calls `onSend` with text
- Test Enter key calls `onSend`
- Test Shift+Enter does not call `onSend`
- Test send button is disabled when empty
- Test send button is disabled when loading
- Test image file selection shows preview
- Use `@testing-library/svelte` and `@testing-library/user-event`

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add ChatInput component with image upload

- Create text input with auto-resize and Enter-to-send
- Add image upload with preview thumbnail
- Disable input during loading state
- Add component tests for input interactions
```

---

### Task 6: Example Prompts Component

**Goal:** Create a component that displays starter prompt suggestions for new users when
the chat is empty.

**Files to Create:**

- `frontend/src/lib/components/ExamplePrompts.svelte`
- `frontend/src/lib/components/ExamplePrompts.test.ts`

**Prerequisites:**

- Task 2 complete (types defined)

**Implementation Steps:**

1. Create `frontend/src/lib/components/ExamplePrompts.svelte`:
   - Display a grid/list of example prompt cards
   - Each card has a short description and an icon or emoji
   - Clicking a card triggers the `onSelect` callback with the prompt text
   - Example prompts (hardcoded):
     - "Generate a sunset over mountains with vibrant colors"
     - "Create a watercolor painting of a cat reading a book"
     - "Design a minimalist logo for a coffee shop"
     - "Draw a futuristic cityscape at night"
   - **Props:**
     - `onSelect: (prompt: string) => void`
   - Styled as a centered grid that disappears when chat has messages

**Verification Checklist:**

- [x] Example prompts are displayed as clickable cards
- [x] Clicking a card calls `onSelect` with the prompt text
- [x] Component passes `svelte-check`

**Testing Instructions:**

Write `frontend/src/lib/components/ExamplePrompts.test.ts`:

- Test that all example prompts are rendered
- Test clicking a prompt calls `onSelect` with correct text

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add ExamplePrompts component with starter suggestions

- Create clickable prompt cards for new users
- Add four example prompts covering generation scenarios
- Add component tests for rendering and click behavior
```

---

### Task 7: Settings Panel Component

**Goal:** Create a collapsible settings panel that exposes the Converse API inference
parameters (maxTokens, temperature, topP, topK).

**Files to Create:**

- `frontend/src/lib/components/SettingsPanel.svelte`
- `frontend/src/lib/components/SettingsPanel.test.ts`

**Prerequisites:**

- Task 2 complete (types defined)

**Implementation Steps:**

1. Create `frontend/src/lib/components/SettingsPanel.svelte`:
   - Collapsible panel (toggles open/closed with a gear icon button)
   - When open, displays sliders/inputs for:
     - `maxTokens` -- number input (label: "Max Tokens")
     - `temperature` -- range slider 0-1 with 0.1 step (label: "Temperature")
     - `topP` -- range slider 0-1 with 0.1 step (label: "Top P")
     - `topK` -- number input (label: "Top K")
   - Each control has a label, current value display, and a reset-to-default button
   - Default values: all empty/undefined (meaning "use model defaults")
   - **Props:**
     - `settings: InferenceConfig` -- current settings (bindable)
     - `onChange: (settings: InferenceConfig) => void` -- callback on change
   - Panel slides down/up with a CSS transition

**Verification Checklist:**

- [x] Panel toggles open/closed
- [x] Sliders and inputs update settings values
- [x] Reset buttons clear individual settings
- [x] Component passes `svelte-check`

**Testing Instructions:**

Write `frontend/src/lib/components/SettingsPanel.test.ts`:

- Test panel is initially collapsed
- Test clicking gear icon opens panel
- Test temperature slider updates value
- Test reset button clears a setting
- Test `onChange` is called when settings change

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add collapsible SettingsPanel for inference config

- Create collapsible panel with gear icon toggle
- Add controls for maxTokens, temperature, topP, topK
- Add reset-to-default buttons for each setting
- Add component tests for toggle, input, and reset
```

---

### Task 8: Main Chat Page

**Goal:** Assemble the main chat page that combines all components: message list, input
area, example prompts, and settings panel.

**Files to Create:**

- `frontend/src/routes/+page.svelte` -- Main page component
- `frontend/src/routes/+layout.svelte` -- Root layout with global styles

**Prerequisites:**

- Tasks 3-7 complete

**Implementation Steps:**

1. Create `frontend/src/routes/+layout.svelte`:
   - Minimal layout that renders `{@render children()}`
   - Import and apply global CSS:
     - CSS reset (box-sizing, margin, padding)
     - Set body font-family, background color, color
     - Dark theme by default (dark background, light text) -- this is an image
       generation app, dark backgrounds make images pop

1. Create `frontend/src/routes/+page.svelte`:
   - Initialize the chat store from `$lib/stores/chat.svelte.ts`
   - **Layout structure:**
     - Header bar: "Omni Image" title + settings gear icon (opens SettingsPanel)
     - Main area (scrollable): message list OR example prompts (when no messages)
     - Footer area (fixed): ChatInput component
   - **Message list:**
     - Iterate over `store.messages`, render `ChatMessage` for each
     - Auto-scroll to bottom when new messages are added (use `$effect` to watch
       messages length and scroll)
   - **Example prompts:**
     - Show `ExamplePrompts` when `!store.hasMessages`
     - On select, call `store.sendMessage(prompt)` with the selected prompt text
   - **Settings panel:**
     - Render `SettingsPanel` in the header area
     - Pass `store.settings` and `store.updateSettings`
   - **Error display:**
     - If `store.error` is set, show an error banner above the input with a dismiss
       button
   - **Chat input:**
     - Pass `store.sendMessage` as `onSend`
     - Pass `store.isLoading` as `isLoading`

**Verification Checklist:**

- [x] Page renders with header, message area, and input
- [x] Example prompts show when no messages
- [x] Example prompts disappear after first message
- [x] Messages display in correct order with auto-scroll
- [x] Settings panel opens/closes
- [x] Error banner shows and dismisses
- [x] `svelte-check` passes
- [x] `pnpm build` succeeds

**Testing Instructions:**

Write `frontend/src/routes/page.test.ts` (note: test files do NOT use the `+` prefix
because they are not SvelteKit route modules -- only files that SvelteKit processes as
routes use `+page.svelte`, `+layout.svelte`, etc.; test files are plain TypeScript picked
up by vitest):

- Test initial render shows example prompts
- Test after sending a message, example prompts are hidden
- Test error banner appears on error state
- Test error banner dismiss clears error
- Mock the API module to prevent real network calls

Run: `cd frontend && pnpm test`

**Commit Message Template:**

```text
feat(frontend): add main chat page assembling all components

- Create root layout with dark theme global styles
- Create main page with message list, input, and example prompts
- Add auto-scroll on new messages
- Add error banner with dismiss
- Integrate settings panel in header
- Add page-level tests
```

---

### Task 9: Global Styles

**Goal:** Create the global CSS file with CSS custom properties and base styles. Components
created in Tasks 4-8 use scoped styles with hardcoded values. This task creates a global
stylesheet that sets base element styles (body, html, scrollbar, focus rings) and defines
CSS custom properties. Components are NOT modified -- they keep their existing scoped
styles. The CSS custom properties are available for future use or for the engineer to
reference when building the components in Tasks 4-8 (if building in a single pass).

**Files to Create:**

- `frontend/src/app.css` -- Global styles (imported by layout)

**Files to Modify:**

- `frontend/src/routes/+layout.svelte` -- Add import for `../app.css`

**Prerequisites:**

- Task 8 complete

**Implementation Steps:**

1. Create `frontend/src/app.css` with:
   - CSS custom properties (variables) on `:root`:
     - `--color-bg: #1a1a2e` (dark navy)
     - `--color-surface: #16213e` (slightly lighter)
     - `--color-primary: #0f3460` (blue accent)
     - `--color-accent: #e94560` (coral/red accent for buttons)
     - `--color-text: #eee`
     - `--color-text-muted: #888`
     - `--radius-sm: 4px`
     - `--radius-md: 8px`
     - `--radius-lg: 16px`
     - `--spacing-xs: 4px`
     - `--spacing-sm: 8px`
     - `--spacing-md: 16px`
     - `--spacing-lg: 24px`
     - `--spacing-xl: 32px`
   - Base element styles:
     - `*, *::before, *::after { box-sizing: border-box; }`
     - `body, html { margin: 0; padding: 0; height: 100%; }`
     - `body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: var(--color-bg); color: var(--color-text); }`
   - Scrollbar styling for webkit browsers (dark-themed thin scrollbar)
   - Focus styles: `*:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }`

1. Update `frontend/src/routes/+layout.svelte`:
   - Add `import '../app.css';` at the top of the `<script>` block
   - No other changes to `+layout.svelte`

   Note: Do NOT modify any component files (ChatMessage, ChatInput, ExamplePrompts,
   SettingsPanel, +page.svelte). They retain their existing scoped styles. The CSS
   custom properties defined in `app.css` cascade to all components via `:root`, so
   components can optionally reference them (e.g., `var(--color-accent)`), but this
   is not required for this task.

**Verification Checklist:**

- [x] `frontend/src/app.css` exists with all listed CSS custom properties
- [x] `+layout.svelte` imports `../app.css`
- [x] No component files are modified by this task
- [x] Body has dark background and light text
- [x] Focus rings are visible on interactive elements
- [x] `pnpm build` succeeds

**Testing Instructions:**

No new tests for styling. Verify visually by running `cd frontend && pnpm dev` and
inspecting in a browser at various viewport sizes.

**Commit Message Template:**

```text
style(frontend): add global CSS with dark theme and responsive design

- Create CSS custom properties for consistent theming
- Add dark color scheme optimized for image display
- Add responsive layout for mobile and desktop
- Polish component styles for visual consistency
```

---

### Task 10: Frontend .env.example and Build Verification

**Goal:** Create the frontend `.env.example` and verify the full build pipeline works.

**Files to Create:**

- `frontend/.env.example`

**Prerequisites:**

- Task 9 complete

**Implementation Steps:**

1. Create `frontend/.env.example`:

   ```text
   # API Gateway URL for the backend (required)
   # Set by the deploy script or manually after backend deployment
   PUBLIC_API_URL=https://your-api-id.execute-api.us-west-2.amazonaws.com
   ```

1. Verify the complete frontend build:

   ```bash
   cd frontend
   echo "PUBLIC_API_URL=http://localhost:8000" > .env
   pnpm install
   pnpm run lint
   pnpm run format:check
   pnpm run check
   pnpm run test
   pnpm run build
   ```

1. Verify the built output:
   - `frontend/build/` contains `index.html`, `200.html` (SPA fallback), and assets
   - No build warnings or errors

**Verification Checklist:**

- [x] `.env.example` documents all required env vars
- [x] `pnpm lint` passes
- [x] `pnpm format:check` passes
- [x] `pnpm check` passes (svelte-check)
- [x] `pnpm test` passes
- [x] `pnpm build` succeeds

**Testing Instructions:**

No new tests. This task is a verification/integration step.

**Commit Message Template:**

```text
docs(frontend): add .env.example and verify build pipeline

- Create frontend .env.example with API URL documentation
- Verify lint, type check, test, and build all pass
```

---

### Task 11: Add Frontend CI Jobs to GitHub Actions

**Goal:** Add frontend lint, type check, and test jobs to the existing CI workflow created
in Phase 1 Task 12. This was deferred from Phase 1 because the `frontend/` directory did
not exist yet -- running these jobs without the directory would cause CI failures.

**Files to Modify:**

- `.github/workflows/ci.yml`

**Prerequisites:**

- Phase 1 Task 12 complete (CI workflow exists with backend-only jobs)
- Phase 2 Tasks 1-10 complete (frontend directory and all code exist)

**Implementation Steps:**

1. Edit `.github/workflows/ci.yml` to add three new jobs:
   - `frontend-lint`:
     - Setup Node.js 20, install pnpm
     - `cd frontend && pnpm install`
     - `cd frontend && pnpm run lint`
     - `cd frontend && pnpm run format:check`
   - `frontend-check`:
     - Setup Node.js 20, install pnpm
     - `cd frontend && pnpm install`
     - `cd frontend && pnpm run check`
   - `frontend-test`:
     - Setup Node.js 20, install pnpm
     - `cd frontend && pnpm install`
     - `cd frontend && pnpm run test`

1. Update the `all-checks` job:
   - Add `frontend-lint`, `frontend-check`, `frontend-test` to the `needs` list
   - Add failure checks for the new jobs in the verification step

**Verification Checklist:**

- [x] CI YAML is valid after edits
- [x] Frontend jobs use Node.js 20 and pnpm
- [x] `all-checks` job depends on all backend AND frontend jobs
- [x] Frontend jobs run in parallel with backend jobs

**Testing Instructions:**

No automated tests. Push to a branch and verify all CI jobs pass in GitHub Actions.

**Commit Message Template:**

```text
ci: add frontend lint, check, and test jobs to CI workflow

- Add frontend-lint job (eslint + prettier)
- Add frontend-check job (svelte-check)
- Add frontend-test job (vitest)
- Update all-checks gate to include frontend jobs
```

## Phase Verification

After completing all tasks in Phase 2:

1. **Run the full frontend test suite:**

   ```bash
   cd frontend
   pnpm test
   ```

   All tests must pass.

1. **Run linting and type checking:**

   ```bash
   cd frontend
   pnpm run lint
   pnpm run format:check
   pnpm run check
   ```

   Zero errors on all commands.

1. **Build the static site:**

   ```bash
   cd frontend
   pnpm run build
   ```

   Must succeed with output in `frontend/build/`.

1. **Verify project structure:**

   ```text
   frontend/
     .env.example
     amplify.yml
     eslint.config.js
     package.json
     svelte.config.js
     tsconfig.json
     vite.config.ts
     vitest.config.ts
     .prettierrc
     .prettierignore
     static/
       favicon.png
     src/
       app.css
       app.d.ts
       app.html
       lib/
         api.ts
         api.test.ts
         config.ts
         types.ts
         components/
           ChatInput.svelte
           ChatInput.test.ts
           ChatMessage.svelte
           ChatMessage.test.ts
           ExamplePrompts.svelte
           ExamplePrompts.test.ts
           SettingsPanel.svelte
           SettingsPanel.test.ts
         stores/
           chat.svelte.ts
           chat.svelte.test.ts
       routes/
         +layout.svelte
         +page.svelte
         page.test.ts
   ```

1. **End-to-end smoke test** (manual, requires deployed backend):
   - Run `pnpm dev`, open in browser
   - Click an example prompt -- verify it sends and displays a response
   - Type a custom prompt -- verify response with image
   - Upload an image with an edit instruction -- verify edited image response
   - Open settings, adjust temperature, send another prompt
   - Verify rate limit error appears after 10 requests (if testing against a fresh bucket)

## Known Limitations

- **No multi-turn memory on backend** -- the frontend sends the full conversation history
  with each request. For very long conversations, this may hit token limits or increase
  latency. No truncation strategy is implemented in this phase.
- **No image download button** -- users cannot directly download generated images (they
  can right-click and save). This could be a future enhancement.
- **No conversation persistence** -- chat history is lost on page refresh. This is by
  design (stateless demo app).
- **No offline support** -- requires network connectivity to the deployed backend.
- **Settings ranges are not validated against model limits** -- the exact valid ranges for
  Nova 2 Omni inference parameters are not fully documented. Invalid values will result in
  API errors displayed to the user.
