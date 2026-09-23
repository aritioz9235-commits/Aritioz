# Aritioz Project Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Start a project open an Aritioz-branded, ChatGPT-inspired workspace while retaining chat and image attachment behavior.

**Architecture:** Rebuild `LaunchOSWorkspace` markup around the reference layout while retaining its current state and API helpers. Add only scoped workspace CSS and source-level Vitest regressions, following the project’s existing Node test convention.

**Tech Stack:** React 19, TypeScript, Vinext/Vite, custom CSS, Lucide React, Vitest.

**Spec:** `docs/superpowers/specs/2026-09-23-aritioz-project-workspace-design.md`

## Global Constraints

- Display **Aritioz** at the upper-left in place of the reference screenshot’s ChatGPT label.
- Preserve API submission, image validation/preview, loading, errors, response metadata, New chat reset, Work mode, and mobile navigation.
- Do not add dependencies, billing, account management, real voice input, web search, or image generation.
- Keep keyboard access, visible focus, narrow-screen usability, and a white/black/gray UI with cobalt accent.

## Review Focus

- Whitespace-only prompts must not submit.
- API errors must remain readable and New chat must clear them.
- Invalid attachments must show existing validation feedback.
- Mobile navigation must not obscure the composer or cause overflow.
- Reduced-motion users must retain all usable controls.

## File Structure

- `components/launchos-workspace.tsx` — client workspace markup, state, and API wiring.
- `components/launchos-workspace.test.ts` — source-level UI contract tests.
- `app/globals.css` — scoped workspace visual and responsive rules.

### Task 1: Create a failing Aritioz workspace contract

**Files:**
- Create: `components/launchos-workspace.test.ts`
- Modify: `components/launchos-workspace.tsx`

**Interfaces:**
- Consumes: `LaunchOSWorkspace`, `sendChatMessage`, `readImageFile`.
- Produces: tests for Aritioz identity, empty state, starter actions, tabs, guarded send, and New chat reset.

- [ ] **Step 1: Write the failing test**

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const workspace = readFileSync(new URL('./launchos-workspace.tsx', import.meta.url), 'utf8');

describe('Aritioz project workspace', () => {
  it('shows Aritioz above the reference-inspired empty state', () => {
    expect(workspace).toContain('aria-label="Aritioz workspace"');
    expect(workspace).toContain('>Aritioz</span>');
    expect(workspace).toContain("What's on the agenda today?");
    expect(workspace).toContain('Create an image or sticker');
    expect(workspace).toContain('Write or edit');
    expect(workspace).toContain('Search the web');
  });
});
```

- [ ] **Step 2: Verify red**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: FAIL because the exact new empty-state contract is absent.

- [ ] **Step 3: Implement the smallest matching component change**

Retain all existing request state/functions. Replace the top-level semantic landmark and empty-state markup with an Aritioz sidebar, Chat/Work tablist, agenda heading, composer, and three starter buttons. The sidebar must contain Images, Library, Scheduled, Plugins, Projects, Codex, More, profile, and Upgrade; New chat calls the current `startNewProject` function. Each starter action calls `setPrompt` with a useful request.

```tsx
<section className="aritioz-chat" aria-label="Aritioz workspace">
  <aside className={`chat-sidebar${sidebarOpen ? ' mobile-open' : ''}`}>
    <div className="chat-sidebar-brand"><Sparkles aria-hidden="true" size={18} /><span>Aritioz</span></div>
    <button className="new-project-button" onClick={startNewProject}>New chat</button>
  </aside>
</section>
```

- [ ] **Step 4: Verify green**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add components/launchos-workspace.tsx components/launchos-workspace.test.ts && git commit -m "feat: add Aritioz project workspace structure"`

### Task 2: Preserve interaction and accessibility contracts

**Files:**
- Modify: `components/launchos-workspace.test.ts`
- Modify: `components/launchos-workspace.tsx`

**Interfaces:**
- Consumes: Task 1 markup and existing state functions.
- Produces: accessible Chat/Work state, guarded send behavior, and retained attachment/status response flow.

- [ ] **Step 1: Write failing interaction tests**

```ts
it('guards sending and resets through New chat', () => {
  expect(workspace).toContain('if (!value || loading) return;');
  expect(workspace).toContain('onClick={startNewProject}');
  expect(workspace).toContain('disabled={loading || imageLoading || !prompt.trim()}');
  expect(workspace).toContain('setImage(null);');
});

it('provides accessible Chat and Work tabs', () => {
  expect(workspace).toContain('role="tablist"');
  expect(workspace).toContain("aria-selected={mode === 'chat'}");
  expect(workspace).toContain("aria-selected={mode === 'work'}");
});
```

- [ ] **Step 2: Verify red**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: FAIL until the redesigned composer and tabs retain the exact contracts.

- [ ] **Step 3: Implement the minimal interaction markup**

Keep `submitPrompt`, `selectImage`, `startNewProject`, image status, API error, response metadata, and `aria-live` response region. Give the composer `Ask anything` as placeholder, attachment button `aria-label="Add an image"`, Think and voice buttons, and the existing disabled send expression. Use true tab buttons for Chat/Work and distinct Work copy.

- [ ] **Step 4: Verify green**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add components/launchos-workspace.tsx components/launchos-workspace.test.ts && git commit -m "feat: preserve Aritioz workspace interactions"`

### Task 3: Apply the reference visual system responsively

**Files:**
- Modify: `components/launchos-workspace.test.ts`
- Modify: `app/globals.css`

**Interfaces:**
- Consumes: class names and controls created in Tasks 1–2.
- Produces: white desktop layout, mobile overlay navigation, focus outline, and reduced-motion fallback.

- [ ] **Step 1: Write a failing stylesheet test**

```ts
it('defines responsive and reduced-motion workspace styling', () => {
  const css = readFileSync(new URL('../app/globals.css', import.meta.url), 'utf8');
  expect(css).toContain('.aritioz-chat');
  expect(css).toContain('.chat-sidebar');
  expect(css).toContain('@media (max-width: 760px)');
  expect(css).toContain('@media (prefers-reduced-motion: reduce)');
  expect(css).toContain(':focus-visible');
});
```

- [ ] **Step 2: Verify red**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: FAIL if the full responsive/accessibility stylesheet contract is absent.

- [ ] **Step 3: Add scoped styles**

```css
.aritioz-chat {
  min-height: min(760px, 82vh);
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  overflow: hidden;
  color: #171717;
  background: #fff;
}
.aritioz-chat :focus-visible { outline: 2px solid #3478f6; outline-offset: 3px; }
```

Style sidebar, selected New chat action, tabs, centered canvas, composer, shortcuts, response, attachments, profile, and blue send action. At 760px make the sidebar a `.mobile-open` overlay. Under reduced motion disable workspace transitions.

- [ ] **Step 4: Verify green**

Run: `npm test -- components/launchos-workspace.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add app/globals.css components/launchos-workspace.test.ts && git commit -m "style: match Aritioz project workspace reference"`

### Task 4: Verify the integrated workspace

**Files:**
- Verify: `components/launchos-workspace.tsx`
- Verify: `components/launchos-workspace.test.ts`
- Verify: `app/globals.css`

**Interfaces:**
- Consumes: completed markup, behavior, and styles.
- Produces: verified local workspace.

- [ ] **Step 1: Run all tests**

Run: `npm test`

Expected: PASS with no Vitest failures.

- [ ] **Step 2: Run lint**

Run: `npm run lint`

Expected: PASS with no lint errors.

- [ ] **Step 3: Build production output**

Run: `npm run build`

Expected: exit code 0.

- [ ] **Step 4: Browser-check Start a project**

Verify the upper-left Aritioz label, agenda empty state, three shortcuts, Chat/Work tabs, prompt response/error state, New chat reset, and mobile sidebar behavior.

- [ ] **Step 5: Commit corrections if browser checking requires them**

Run: `git add components/launchos-workspace.tsx components/launchos-workspace.test.ts app/globals.css && git commit -m "fix: finalize Aritioz project workspace"`
