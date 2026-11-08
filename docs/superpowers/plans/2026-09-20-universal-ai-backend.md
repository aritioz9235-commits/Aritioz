# Universal AI Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a secure, local-first multi-provider AI gateway and connect the existing Ask Aritioz workspace to real same-page streamed responses.

**Architecture:** Server-only provider registry loads validated environment configuration, discovers models dynamically, and normalizes Ollama NDJSON and OpenAI-compatible SSE into browser-facing SSE. The existing client loads provider/model state from the gateway and keeps a cancellable conversation transcript; it never receives provider URLs or credentials.

**Tech Stack:** Vinext/React 19, TypeScript, Cloudflare-compatible Fetch/ReadableStream APIs, Vitest, local Ollama, optional OpenAI-compatible runtime adapters.

**Spec:** `docs/superpowers/specs/2026-09-20-universal-ai-backend-design.md`

## Global Constraints

- Preserve unrelated Aritioz design and existing user changes.
- Default to local `ollama-local` at `http://127.0.0.1:11434`; no cloud provider is enabled by default.
- Provider keys, private URLs, upstream stack traces, and conversation content must never reach browser logs or API responses.
- Do not download models, fabricate responses, silently switch models, or follow upstream redirects.
- Hosted `localhost` is the backend host, not a developer laptop; document private-network/tunnel deployment.
- Real provider verification is only reported for reachable configured models; discovery is not generation verification.

## Review Focus

- Fragmented UTF-8 NDJSON and SSE chunks must reconstruct one exact streamed response; Task 3 parser tests cover this.
- A malicious/redirecting provider URL must not be fetched; Task 2 config tests cover this.
- A cancelled browser request must abort upstream and retain a visibly interrupted partial response; Tasks 4 and 5 cover this.
- Missing runtime/key must show an honest setup error, never a mock answer; Tasks 3 and 5 cover this.
- A provider/model ID must be validated server-side and cannot be replaced by an automatic fallback; Task 4 route tests cover this.

## File Structure

- `lib/ai/types.ts`: shared provider, model, request, capability, and normalized-stream types.
- `lib/ai/config.ts`: server-only environment parsing, default local Ollama profile, URL/secret safety validation.
- `lib/ai/providers.ts`: provider interface and registry construction.
- `lib/ai/ollama.ts`: Ollama discovery/chat/NDJSON parser.
- `lib/ai/openai-compatible.ts`: reusable discovery/chat/SSE parser used by llama.cpp, vLLM, LocalAI, TGI, SGLang, and generic profiles.
- `lib/ai/stream.ts`: browser SSE serializer and upstream abort/error normalization.
- `lib/ai/rate-limit.ts`: in-memory local-development concurrency/rate limiter.
- `app/api/**/route.ts`: health, discovery, chat, streaming, and admin-test route handlers.
- `components/launchos-workspace.tsx`: real chat state, picker, streaming/cancel/copy/retry UI.
- `app/globals.css`: focused workspace UI styles.
- `.env.example`: safe placeholder configuration; local Ollama enabled, all remote profiles disabled.
- `README.md` and `BACKEND_VERIFICATION.md`: setup, deployment, API, and evidence.
- `lib/ai/*.test.ts`, `app/api/**/*.test.ts`, `components/*.test.tsx`: automated coverage.

### Task 1: Establish test tooling and safe configuration

**Files:**
- Create: `.env.example`, `lib/ai/types.ts`, `lib/ai/config.ts`, `lib/ai/config.test.ts`
- Modify: `package.json`, `package-lock.json`, `.gitignore`

**Interfaces:**
- Produces `loadAIConfig(env: Record<string, string | undefined>): AIConfig` and `ProviderConfig` for all later provider/route code.
- Produces `AI_PROVIDER_CONFIG` configuration contract with `id`, `type`, `baseUrl`, `enabled`, `apiKeyEnv`, `maxConcurrency`, and `timeoutMs`.

- [ ] **Step 1: Add Vitest commands and write failing configuration tests**

```ts
import { describe, expect, it } from 'vitest';
import { loadAIConfig } from './config';

describe('loadAIConfig', () => {
  it('enables only the default loopback Ollama provider with an empty environment', () => {
    expect(loadAIConfig({}).providers).toEqual([
      expect.objectContaining({ id: 'ollama-local', type: 'ollama', enabled: true }),
    ]);
  });

  it('disables an enabled provider with a missing required key without revealing its URL', () => {
    const result = loadAIConfig({ AI_PROVIDER_CONFIG: JSON.stringify([{ id: 'remote', type: 'openai-compatible', baseUrl: 'https://models.example/v1', enabled: true, apiKeyEnv: 'REMOTE_KEY' }]) });
    expect(result.providers[0]).toMatchObject({ id: 'remote', enabled: false, status: 'disabled' });
  });

  it.each(['file:///etc/passwd', 'http://169.254.169.254/latest', 'https://models.example/redirect'])('rejects unsafe provider URLs: %s', (baseUrl) => {
    expect(() => loadAIConfig({ AI_PROVIDER_CONFIG: JSON.stringify([{ id: 'unsafe', type: 'ollama', baseUrl, enabled: true }]) })).toThrow(/provider URL/i);
  });
});
```

- [ ] **Step 2: Run the configuration test to verify it fails because the module and test command do not exist**

Run: `npm test -- lib/ai/config.test.ts`

Expected: FAIL with a missing `test` script/module error.

- [ ] **Step 3: Install locked test dependencies and implement the typed config parser**

Add scripts `test`, `test:watch`, and `typecheck`; use Vitest with Node environment. Define no public environment variables for provider URLs/keys. Parse the private `AI_PROVIDER_CONFIG` JSON, preserve only safe status/message fields for browser output, block non-HTTP(S), loopback metadata/link-local/private targets except explicit default local Ollama, duplicate IDs, URL credentials, redirects, and missing enabled-provider key values. Create `.env.example` with placeholder keys, optional disabled profiles for Ollama, llama.cpp, vLLM, LocalAI, TGI, SGLang, LM Studio, and configured-but-disabled hosted providers.

```ts
export type ProviderType = 'ollama' | 'openai-compatible' | 'llama-cpp' | 'vllm' | 'localai' | 'tgi' | 'sglang' | 'lm-studio';
export function loadAIConfig(env: Record<string, string | undefined>): AIConfig { /* validated result */ }
```

- [ ] **Step 4: Run focused tests, typecheck, and commit**

Run: `npm test -- lib/ai/config.test.ts && npm run typecheck`

Expected: PASS.

```bash
git add package.json package-lock.json .gitignore .env.example lib/ai/types.ts lib/ai/config.ts lib/ai/config.test.ts
git commit -m "feat: add secure AI provider configuration"
```

### Task 2: Build provider registry and dynamic model discovery

**Files:**
- Create: `lib/ai/providers.ts`, `lib/ai/ollama.ts`, `lib/ai/openai-compatible.ts`, `lib/ai/providers.test.ts`

**Interfaces:**
- Consumes `AIConfig` and `ProviderConfig` from Task 1.
- Produces `ProviderRegistry.listProviders(): Promise<BrowserProvider[]>`, `listModels(): Promise<BrowserModel[]>`, and `getProvider(id): AIProvider | undefined`.

- [ ] **Step 1: Write failing adapter and registry tests**

```ts
it('discovers Ollama model metadata from /api/tags', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ models: [{ name: 'qwen3:4b', size: 123, details: { family: 'qwen3' } }] })));
  await expect(new OllamaProvider(config, fetcher).listModels()).resolves.toEqual([
    expect.objectContaining({ providerId: 'ollama-local', modelId: 'qwen3:4b', chat: 'supported', streaming: 'supported' }),
  ]);
});

it('marks a failed optional provider unreachable while leaving reachable providers available', async () => {
  await expect(registry.listProviders()).resolves.toEqual(expect.arrayContaining([
    expect.objectContaining({ id: 'optional', status: 'unreachable' }),
  ]));
});
```

- [ ] **Step 2: Run adapter tests and verify they fail for missing classes**

Run: `npm test -- lib/ai/providers.test.ts`

Expected: FAIL with missing provider imports.

- [ ] **Step 3: Implement one common provider interface and concrete adapters**

Implement `AIProvider` with `healthCheck`, `listModels`, `chat`, `streamChat`, and `capabilities`. Implement native Ollama `/api/tags` and `/api/chat`; implement OpenAI-compatible `/models` and `/chat/completions`. Make runtime-specific types instantiate the generic adapter with declared endpoint profiles rather than duplicate code. Keep capability state `supported | unsupported | unknown`; only mark chat/streaming supported where the chosen configured path is known compatible. Give each upstream fetch an abort signal, no redirect policy, trusted base URL, and timeout.

- [ ] **Step 4: Run tests and commit**

Run: `npm test -- lib/ai/providers.test.ts && npm run typecheck`

Expected: PASS.

```bash
git add lib/ai/providers.ts lib/ai/ollama.ts lib/ai/openai-compatible.ts lib/ai/providers.test.ts
git commit -m "feat: add dynamic AI provider registry"
```

### Task 3: Normalize upstream streams and expose secure discovery/health routes

**Files:**
- Create: `lib/ai/stream.ts`, `lib/ai/stream.test.ts`, `lib/ai/rate-limit.ts`, `app/health/live/route.ts`, `app/health/ready/route.ts`, `app/api/ai/providers/route.ts`, `app/api/ai/models/route.ts`

**Interfaces:**
- Consumes `ProviderRegistry` from Task 2.
- Produces `parseOllamaNDJSON`, `parseOpenAICompatibleSSE`, `toBrowserSSE`, `createRequestGate`, and browser-safe GET endpoints.

- [ ] **Step 1: Write failing fragmented-stream and safe-response tests**

```ts
it('reassembles split UTF-8 Ollama NDJSON text without loss', async () => {
  const body = streamFrom(['{"message":{"content":"caf', 'é"},"done":false}\n', '{"done":true}\n']);
  await expect(collect(parseOllamaNDJSON(body))).resolves.toEqual([
    { type: 'text', text: 'café' }, { type: 'done' },
  ]);
});

it('does not include key names, URLs, or upstream body in a browser provider error', async () => {
  expect(toBrowserProviderError(new Error('https://secret-host key=abc'))).toEqual({ code: 'PROVIDER_UNAVAILABLE', message: expect.not.stringMatching(/secret|abc/) });
});
```

- [ ] **Step 2: Run tests and verify expected failure**

Run: `npm test -- lib/ai/stream.test.ts`

Expected: FAIL with missing parser functions.

- [ ] **Step 3: Implement parsers, request gate, and GET route handlers**

Decode with streaming `TextDecoder`, buffer incomplete lines/events, normalize only text/error/done frames, and encode browser events as `event: text|error|done`. Add a local in-memory token-bucket/IP concurrency gate and bounded queue; return a generic `429` when full. Ensure health liveness never calls a provider and readiness exposes only a boolean/status count. Ensure provider/model routes expose IDs, display names, capabilities, and status but no base URL, keys, or raw upstream detail.

- [ ] **Step 4: Run tests, route typecheck, and commit**

Run: `npm test -- lib/ai/stream.test.ts && npm run typecheck`

Expected: PASS.

```bash
git add lib/ai/stream.ts lib/ai/stream.test.ts lib/ai/rate-limit.ts app/health app/api/ai/providers app/api/ai/models
git commit -m "feat: expose safe AI discovery and health routes"
```

### Task 4: Implement validated chat and stream routes

**Files:**
- Create: `lib/ai/request.ts`, `lib/ai/request.test.ts`, `app/api/ai/chat/route.ts`, `app/api/ai/chat/stream/route.ts`, `app/api/ai/test/route.ts`, `app/api/ai/chat/route.test.ts`

**Interfaces:**
- Consumes registry, stream, and rate-gate APIs from Tasks 2–3.
- Produces non-streamed JSON chat, streamed SSE chat, and opt-in admin smoke-test endpoints.

- [ ] **Step 1: Write failing request/route tests**

```ts
it('rejects a request that names a model not discovered by its selected provider', async () => {
  const response = await POST(jsonRequest({ providerId: 'ollama-local', modelId: 'unknown', messages: [{ role: 'user', content: 'Hi' }] }));
  expect(response.status).toBe(400);
  await expect(response.json()).resolves.toEqual({ error: { code: 'MODEL_UNAVAILABLE', message: expect.any(String) } });
});

it('aborts upstream streaming when the client signal aborts', async () => {
  const abort = new AbortController();
  const response = await streamPost(jsonRequest(validRequest, abort.signal));
  abort.abort();
  await expect(readAll(response.body!)).resolves.toContain('event: interrupted');
  expect(upstreamAbortSpy).toHaveBeenCalledOnce();
});
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `npm test -- lib/ai/request.test.ts app/api/ai/chat/route.test.ts`

Expected: FAIL with missing route validators/handlers.

- [ ] **Step 3: Implement request validation and route behavior**

Accept only `providerId`, `modelId`, and bounded `user|assistant|system` text messages; cap body bytes, number of messages, and per-message characters. Require an exact selected enabled provider/model and reject capability-confirmed unsupported streaming. Wire request abort to upstream abort; emit partial text followed by `interrupted` without retrying. Return generic error codes (`INVALID_REQUEST`, `MODEL_UNAVAILABLE`, `PROVIDER_UNAVAILABLE`, `TIMEOUT`, `RATE_LIMITED`, `OUT_OF_MEMORY`) with setup guidance but no upstream detail. Make `/api/ai/test` return `404` unless `AI_ADMIN_TEST_SECRET` exists and the supplied server-only authorization header matches it.

- [ ] **Step 4: Run route tests and commit**

Run: `npm test -- lib/ai/request.test.ts app/api/ai/chat/route.test.ts && npm run typecheck`

Expected: PASS.

```bash
git add lib/ai/request.ts lib/ai/request.test.ts app/api/ai/chat app/api/ai/test
git commit -m "feat: add validated AI chat endpoints"
```

### Task 5: Connect the same-page workspace to real streaming chat

**Files:**
- Modify: `components/launchos-workspace.tsx`, `app/globals.css`
- Create: `components/launchos-workspace.test.tsx`

**Interfaces:**
- Consumes browser-safe `GET /api/ai/models`, `GET /api/ai/providers`, and SSE `POST /api/ai/chat/stream` from Tasks 3–4.
- Produces a selectable-provider/model, streaming, cancellable same-page conversation UI.

- [ ] **Step 1: Write failing workspace behavior tests**

```tsx
it('shows setup guidance rather than a response when no model is available', async () => {
  mockModels([]);
  render(<LaunchOSWorkspace />);
  expect(await screen.findByText(/install Ollama or configure an enabled provider/i)).toBeVisible();
});

it('appends streamed text and marks a stopped response interrupted', async () => {
  mockModels([availableModel]);
  mockSSE(['event: text\ndata: {"text":"Hello"}\n\n']);
  render(<LaunchOSWorkspace />);
  await send('Hi');
  expect(await screen.findByText('Hello')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: /stop generation/i }));
  expect(await screen.findByText(/interrupted/i)).toBeVisible();
});
```

- [ ] **Step 2: Run component tests and verify they fail**

Run: `npm test -- components/launchos-workspace.test.tsx`

Expected: FAIL because model loading/stream controls do not yet exist.

- [ ] **Step 3: Implement the UI without changing unrelated layout**

Replace the current fake submitted response with typed transcript state and `fetch` to the internal routes. Populate a model selector with `{ providerId, modelId }`; display the chosen provider/model. Parse only gateway SSE, update partial text incrementally, prevent a second submission during generation, and use `AbortController` for Stop. Add Copy, Retry using the exact last request, safe escaped Markdown/code rendering, Shift+Enter newline in a textarea, and inline setup/error guidance. Do not add client-side provider fallbacks or keys.

- [ ] **Step 4: Run component tests, lint/typecheck, and commit**

Run: `npm test -- components/launchos-workspace.test.tsx && npm run lint && npm run typecheck`

Expected: PASS.

```bash
git add components/launchos-workspace.tsx components/launchos-workspace.test.tsx app/globals.css
git commit -m "feat: stream Aritioz workspace responses"
```

### Task 6: Verify live behavior and document deployment

**Files:**
- Create: `README.md`, `BACKEND_VERIFICATION.md`
- Modify: `.env.example`

**Interfaces:**
- Consumes all completed routes/UI and configuration.
- Produces exact local/hosted setup instructions and evidence-based verification table.

- [ ] **Step 1: Write failing documentation assertions where practical**

```ts
it('documents no-cloud default and the required Ollama run command', async () => {
  const readme = await readFile('README.md', 'utf8');
  expect(readme).toContain('ollama run');
  expect(readme).toMatch(/no paid provider is enabled by default/i);
});
```

- [ ] **Step 2: Run the documentation test and verify it fails before README exists**

Run: `npm test -- docs.test.ts`

Expected: FAIL with missing README/documentation test fixture.

- [ ] **Step 3: Document exact commands and run verification**

Document `cp .env.example .env`, `ollama serve`, `ollama pull <chosen-model>`, `npm ci`, `npm run dev`, test/build commands, every endpoint, optional remote configuration, and secure hosted connectivity patterns. Attempt `ollama list`; if a model is available, run discovery, non-streamed chat, streamed chat, and same-page browser flow. If it is unavailable, mark it `UNREACHABLE` and record the exact command/output. Test validation, missing runtime, cancellation, and rate limiting. Run `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build`; fix actionable failures and rerun. Use the required provider/model evidence statuses exactly.

- [ ] **Step 4: Commit documentation and verification report**

```bash
git add README.md BACKEND_VERIFICATION.md .env.example docs.test.ts
git commit -m "docs: add AI backend setup and verification report"
```

## Plan self-review

- Spec coverage: provider registry, dynamic discovery, native Ollama and generic profiles, every required route, same-page UI, cancellation, safety controls, deployment, and real-verification status all map to Tasks 1–6.
- Placeholder scan: no implementation placeholders or deferred requirements remain.
- Type consistency: `ProviderConfig` feeds `ProviderRegistry`; `AIProvider` feeds stream/route handlers; route request uses exact `providerId`/`modelId` pair used by the workspace.
- Review focus coverage: fragmented streams (Task 3), SSRF/redirect URLs (Task 1), abort behavior (Tasks 4–5), unavailable runtime (Tasks 2 and 5), and no fallback (Task 4) all have named automated tests.
