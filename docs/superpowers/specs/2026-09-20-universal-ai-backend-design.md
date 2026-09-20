# Universal AI Backend Design

## Goal

Connect the existing Aritioz workspace's **Ask Aritioz** input to a real,
same-page streamed chat backend. Local Ollama is the default integration. Other
self-hosted, open-source inference runtimes are configurable server-side and
disabled unless explicitly configured.

## Scope and constraints

- Preserve the existing landing page and workspace UI outside the chat flow.
- Do not expose provider credentials, provider URLs, or upstream stack traces to
  the browser.
- Do not fetch models, configure paid providers, fabricate responses, silently
  switch providers, or route local traffic to cloud inference.
- No authentication currently exists. The production API will therefore be
  local-development-only by default; documentation will state the authentication,
  network isolation, and rate-limit requirements for public deployment.
- A hosted backend's `localhost` is the host/container running that backend, not
  the developer's laptop. A hosted deployment must use a private network,
  authenticated tunnel, or co-located inference runtime.

## Architecture

### Provider registry

The server will read a validated `AI_PROVIDER_CONFIG` JSON configuration from
the environment. Each instance has a stable provider ID, type, trusted base URL,
enabled state, optional API-key environment-variable name, and timeout/concurrency
limits. The registry creates one adapter per configured instance.

Supported adapter types:

| Type | Discovery | Generation transport |
| --- | --- | --- |
| `ollama` | Ollama `/api/tags` | Ollama NDJSON `/api/chat` |
| `openai-compatible` | configurable `/v1/models` | OpenAI-compatible streaming chat completions |
| `llama-cpp`, `vllm`, `localai`, `tgi`, `sglang` | provider-specific profile or OpenAI-compatible path | their configured compatible endpoint |

The specific runtime names are configuration profiles rather than a promise that
all installed versions expose exactly the same API. At startup/discovery, the
adapter records each model's known, unsupported, or unknown streaming/chat
capabilities. The chat route rejects an operation that a configured adapter has
confirmed unsupported.

Only `ollama-local` is enabled by default. Its base URL defaults to
`http://127.0.0.1:11434`; it has no API key. All remote instances are disabled
until configured with an allowed server-side URL and, if required, an environment
key. Redirects are not followed.

### HTTP API

| Route | Behaviour |
| --- | --- |
| `GET /health/live` | Process liveness; no provider call. |
| `GET /health/ready` | Registry readiness and enabled-provider summary, without private connection details. |
| `GET /api/ai/providers` | Browser-safe provider statuses and capability state. |
| `GET /api/ai/models` | Dynamically discovered browser-safe models, labelled with provider and model IDs. |
| `POST /api/ai/chat` | Validated non-streaming completion for integrations/tests. |
| `POST /api/ai/chat/stream` | Validated SSE stream, forwarding normalized chunks from the selected provider. |
| `POST /api/ai/test` | Disabled unless an administrator secret is configured; accepts the secret only server-side and returns redacted diagnostics. |

Requests accept the exact provider ID and model ID selected by the user. Server
validation applies payload/body limits, message count/content limits, allowed
roles, per-client request limits, concurrency queues, provider timeout, and an
explicit fallback policy (off by default). Upstream URLs come only from server
configuration and must be `http`/`https` and non-redirecting. Conversation
content is not logged.

The streaming route uses a `ReadableStream` and SSE framing. Adapters parse
upstream NDJSON or SSE using streaming UTF-8 decoding, tolerate fragmented
network chunks, normalize text/error/done events, and propagate an abort signal
when the browser cancels or disconnects. Once text is emitted, no retry or
fallback is permitted. Confirmed resource/OOM errors are surfaced as a clear
non-retryable setup/runtime error.

### Frontend

`LaunchOSWorkspace` will load browser-safe provider/model state from the backend
when the dialog opens. It will show:

- a provider/model selector populated only from discovered enabled models;
- a setup state when no local runtime/model is reachable;
- a message transcript with the selected provider/model label;
- streamed assistant text, loading state, Stop, Copy, and Retry controls;
- follow-up history bounded by server validation;
- safe, dependency-free rendering of text and fenced code (escaped before DOM
  insertion; no raw HTML rendering).

Enter submits and Shift+Enter inserts a newline. The UI prevents duplicate
submissions, retains partial text after cancellation, and marks it interrupted.
There is no client-side provider URL/key access and no mock response path.

### Configuration and deployment

`.env.example` will document local Ollama and optional disabled remote profiles,
plus trusted origins, test-admin secret, body/rate/concurrency/time limits, and
the explicit fallback setting. Configuration parsing fails closed: invalid JSON,
unknown provider type, unsafe URL, a missing enabled-provider key, or duplicate
provider ID prevents that provider from becoming available.

Documentation will include local installation/start/model commands and hosted
patterns: deploy an Ollama container/service in the same private network, or
place an authenticated HTTPS reverse proxy/tunnel between the backend and a
private Ollama host. It will explicitly forbid public exposure of port 11434.

### Testing and verification

Unit tests will cover config validation, provider URL safety, adapter parsers for
fragmented NDJSON/SSE, request validation, error redaction, cancellation,
fallback policy, and model status normalization. Route tests will use mocked
upstream servers only where a local runtime is unavailable and label those
results accordingly.

Verification runs dependency installation from the existing lockfile, lint,
typecheck, tests, production build, and backend startup. It attempts live
discovery plus a small real chat and streamed chat against every reachable,
enabled model, sequentially and with safe limits. Browser acceptance is run only
when a reachable runtime and browser tooling are available. The final
`BACKEND_VERIFICATION.md` records results with the required VERIFIED,
MOCK-TESTED ONLY, UNREACHABLE, DISABLED, FAILED, or NOT TESTED status; discovery
alone is never reported as generation verification.

## Files expected to change

- Route handlers and server-only AI modules under `app/api/` and `lib/ai/`.
- `components/launchos-workspace.tsx` and related CSS for same-page chat.
- `.env.example`, setup documentation, test configuration/tests, package scripts
  and dependencies only when required by the selected test/runtime approach.
- `BACKEND_VERIFICATION.md` after implementation and verification.
