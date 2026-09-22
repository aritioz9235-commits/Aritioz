# Aritioz Editorial Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the existing Aritioz site and Seller Commerce OS workspace into a responsive, accessible, editorial creative-intelligence experience without breaking the existing AI chat and attachment behavior.

**Architecture:** Keep Vinext/React 19 and the existing backend client. Replace the monolithic landing-page markup with focused section components, move page and workspace styling into dedicated CSS modules imported by the global stylesheet, and isolate client-side interaction in small client components. Preserve `LaunchOSWorkspace` as the functional product boundary while redesigning its visual hierarchy and adding a meaningful Work mode.

**Tech Stack:** React 19, Vinext, TypeScript 5.9, CSS/Tailwind import pipeline, Lucide React, Vitest, existing Base UI dialog primitives

**Spec:** `docs/superpowers/specs/2026-09-22-aritioz-editorial-redesign-design.md`

## Global Constraints

- Preserve “Aritioz — Creative intelligence for what comes next.” and make “Where ideas become intelligent.” the hero statement.
- Keep the current AI chat, image attachment, mode switching, saved-project selection, and backend response behavior.
- Use warm off-white, deep near-black, muted graphite, and one electric cobalt accent.
- Add no runtime dependency for animation or the generative field.
- Avoid generic SaaS cards, excessive gradients, glassmorphism, neon overload, and robot imagery.
- All hover behavior must have an equivalent keyboard-focus treatment.
- `prefers-reduced-motion` must disable parallax, pointer response, and staggered transitions without hiding content.
- The production build, lint, and test suite must pass without errors.

## Review Focus

- With JavaScript or canvas unavailable, the hero headline, copy, and actions remain visible and readable; Task 3 pins the decorative-only canvas contract.
- With reduced motion enabled, reveal elements are visible and the intelligence field does not animate; Task 3 includes the media-query assertion.
- With an empty, whitespace-only, loading, or failed chat request, the composer and response region expose the correct disabled or error state; Task 6 covers these state transitions.
- At mobile widths, neither the marketing page nor workspace creates horizontal scrolling, and the sidebar drawer can be opened and dismissed by keyboard; Tasks 2 and 6 cover the required structure and CSS.
- When the inquiry form contains missing fields or an email with spaces, submission stays local and exposes field-specific messages; Task 4 tests the validation function directly.

---

## File Map

- `app/page.tsx`: server-rendered page composition only.
- `app/layout.tsx`: metadata, fonts, and root document.
- `app/globals.css`: tokens, reset, shared accessibility rules, and imports.
- `app/marketing.css`: landing-page grid, section composition, responsive rules, and motion.
- `app/workspace.css`: Seller Commerce OS chrome, conversation, project view, and responsive drawer.
- `components/site/site-header.tsx`: sticky navigation and mobile disclosure.
- `components/site/hero.tsx`: hero content and visual composition.
- `components/site/intelligence-field.tsx`: pointer-responsive canvas, reduced-motion aware.
- `components/site/brand-story.tsx`: editorial manifesto.
- `components/site/process-narrative.tsx`: interactive Discover/Design/Deliver story.
- `components/site/capabilities-editorial.tsx`: three distinct capability compositions.
- `components/site/product-showcase.tsx`: case-study framing and embedded workspace.
- `components/site/project-inquiry.tsx`: accessible project form and validation.
- `components/site/closing-cta.tsx`: final conversion section.
- `components/site/site-footer.tsx`: footer navigation and brand line.
- `components/launchos-workspace.tsx`: functional Seller Commerce OS workspace.
- `lib/project-inquiry.ts`: inquiry validation and mailto construction.
- `app/editorial-redesign.test.ts`: static contracts for copy, landmarks, structure, metadata, and CSS safeguards.
- `lib/project-inquiry.test.ts`: form validation and email-handoff tests.
- `components/workspace-state.test.ts`: source-level workspace behavior contracts supported by existing unit-test tooling.

---

### Task 1: Lock the editorial system and metadata

**Files:**
- Modify: `app/layout.tsx`
- Modify: `app/globals.css`
- Create: `app/marketing.css`
- Create: `app/workspace.css`
- Modify: `app/hero-heading.test.ts`
- Create: `app/editorial-redesign.test.ts`

**Interfaces:**
- Produces: CSS custom properties `--ink`, `--paper`, `--graphite`, `--muted`, `--signal`, `--line`, `--display-font`, `--body-font`, `--gutter`, and `--content-max`.
- Produces: global classes `.skip-link`, `.shell`, `.section-label`, `.reveal`, and `.sr-only` used by later components.

- [ ] **Step 1: Replace the narrow hero assertion with failing design-system and metadata contracts**

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const page = readFileSync(new URL('./page.tsx', import.meta.url), 'utf8');
const layout = readFileSync(new URL('./layout.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('./globals.css', import.meta.url), 'utf8');

describe('Aritioz editorial foundation', () => {
  it('keeps the approved brand and hero copy', () => {
    expect(page).toContain('Where ideas become intelligent.');
    expect(page).toContain('Creative intelligence for what comes next.');
  });

  it('publishes descriptive metadata', () => {
    expect(layout).toContain('Aritioz — Creative Intelligence for What Comes Next');
    expect(layout).toContain('strategy, design, and applied AI');
    expect(layout).toContain("openGraph:");
  });

  it('defines the restrained palette and focus treatment', () => {
    for (const token of ['--ink', '--paper', '--graphite', '--signal', '--content-max']) {
      expect(css).toContain(token);
    }
    expect(css).toContain(':focus-visible');
    expect(css).toContain('.skip-link');
  });
});
```

- [ ] **Step 2: Run the foundation test and verify it fails**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: FAIL because the new metadata and editorial tokens are absent.

- [ ] **Step 3: Implement root metadata, font variables, tokens, reset, and stylesheet boundaries**

Use Geist as the readable sans and add a refined local/system display stack without a network font request:

```tsx
export const metadata: Metadata = {
  title: 'Aritioz — Creative Intelligence for What Comes Next',
  description: 'Aritioz combines strategy, design, and applied AI to build intelligent digital experiences.',
  openGraph: {
    title: 'Aritioz — Creative Intelligence for What Comes Next',
    description: 'Strategy, design, and applied AI for ambitious digital products.',
    type: 'website',
  },
};
```

In `globals.css`, import both focused stylesheets and define the exact foundation:

```css
@import 'tailwindcss';
@import './marketing.css';
@import './workspace.css';

:root {
  --ink: #10100f;
  --paper: #f2efe8;
  --graphite: #292a2b;
  --muted: #74736e;
  --signal: #315cff;
  --line: rgba(16, 16, 15, 0.16);
  --display-font: 'Iowan Old Style', 'Baskerville', 'Times New Roman', serif;
  --body-font: var(--font-geist-sans), Arial, sans-serif;
  --gutter: clamp(1.25rem, 4vw, 4.5rem);
  --content-max: 1440px;
}
```

- [ ] **Step 4: Run the foundation test**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit the editorial foundation**

```bash
git add app/layout.tsx app/globals.css app/marketing.css app/workspace.css app/hero-heading.test.ts app/editorial-redesign.test.ts
git commit -m "feat: establish Aritioz editorial design system"
```

### Task 2: Build the semantic page shell and responsive navigation

**Files:**
- Create: `components/site/site-header.tsx`
- Modify: `app/page.tsx`
- Modify: `app/marketing.css`
- Modify: `app/editorial-redesign.test.ts`

**Interfaces:**
- Produces: `SiteHeader(): JSX.Element` with anchors `#story`, `#process`, `#capabilities`, and `#work`.
- Produces: `data-project-inquiry-trigger` on every Start a project button for Task 4.
- Consumes: tokens and `.shell` from Task 1.

- [ ] **Step 1: Add failing semantic and navigation tests**

```ts
const header = readFileSync(new URL('../components/site/site-header.tsx', import.meta.url), 'utf8');

it('provides landmarks, skip navigation, and all primary destinations', () => {
  expect(page).toContain('href="#main-content"');
  expect(page).toContain('<main id="main-content">');
  for (const target of ['#story', '#process', '#capabilities', '#work']) {
    expect(header).toContain(target);
  }
  expect(header).toContain('data-project-inquiry-trigger');
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: FAIL because the new shell and inquiry trigger do not exist.

- [ ] **Step 3: Create the header and reduce `page.tsx` to section composition**

`SiteHeader` is a client component with `menuOpen`, `aria-expanded`, Escape handling, and link clicks that close the mobile menu. `page.tsx` renders the skip link, header, main sections, inquiry dialog, and footer. Do not leave the previous page-wide `Dialog` wrapper in place.

```tsx
export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <SiteHeader />
      <main id="main-content">
        <Hero />
        <BrandStory />
        <ProcessNarrative />
        <CapabilitiesEditorial />
        <ProductShowcase />
        <ClosingCta />
      </main>
      <ProjectInquiry />
      <SiteFooter />
    </>
  );
}
```

- [ ] **Step 4: Add desktop/mobile header styling and verify the test**

At `max-width: 760px`, replace inline links with a positioned menu panel; maintain `min-height: 44px` on controls and ensure the panel width uses `min(22rem, calc(100vw - 2rem))`.

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit the semantic shell**

```bash
git add app/page.tsx app/marketing.css app/editorial-redesign.test.ts components/site/site-header.tsx
git commit -m "feat: add semantic Aritioz page shell"
```

### Task 3: Implement the hero, intelligence field, story, and process

**Files:**
- Create: `components/site/hero.tsx`
- Create: `components/site/intelligence-field.tsx`
- Create: `components/site/brand-story.tsx`
- Create: `components/site/process-narrative.tsx`
- Modify: `app/marketing.css`
- Modify: `app/editorial-redesign.test.ts`

**Interfaces:**
- Produces: `IntelligenceField({ className?: string }): JSX.Element` with `aria-hidden="true"`.
- Produces: `ProcessNarrative(): JSX.Element` using a three-item typed `steps` array and roving tab selection.
- Consumes: `data-project-inquiry-trigger` convention from Task 2.

- [ ] **Step 1: Add failing content, progressive-enhancement, and reduced-motion tests**

```ts
const hero = readFileSync(new URL('../components/site/hero.tsx', import.meta.url), 'utf8');
const field = readFileSync(new URL('../components/site/intelligence-field.tsx', import.meta.url), 'utf8');
const process = readFileSync(new URL('../components/site/process-narrative.tsx', import.meta.url), 'utf8');
const marketingCss = readFileSync(new URL('./marketing.css', import.meta.url), 'utf8');

it('keeps the intelligence visual decorative and content independent', () => {
  expect(field).toContain('aria-hidden="true"');
  expect(hero).toContain('<h1>');
  expect(hero).toContain('href="#work"');
});

it('supports reduced motion without hiding reveals', () => {
  expect(marketingCss).toContain('@media (prefers-reduced-motion: reduce)');
  expect(marketingCss).toMatch(/\.reveal[\s\S]*opacity:\s*1/);
});

it('includes all three process stages', () => {
  for (const stage of ['Discover', 'Design', 'Deliver']) expect(process).toContain(stage);
});
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: FAIL because the components and reduced-motion contract do not exist.

- [ ] **Step 3: Implement the decorative canvas with a no-motion branch**

Use a client component with `canvasRef`, one `requestAnimationFrame` loop, `ResizeObserver`, and pointer coordinates stored in refs. Check `matchMedia('(prefers-reduced-motion: reduce)')`; render a single static frame when true. Cancel the frame and disconnect observers in cleanup. Clamp device pixel ratio to `2` and use at most `42` points on desktop and `24` below 760px.

- [ ] **Step 4: Implement editorial hero, story, and interactive process**

The hero has one `h1`, both approved CTAs, the brand line, and a scroll cue. Brand Story uses the approved definition copy. Process renders all step content in the DOM; button selection changes the emphasized stage but never gates access to text.

- [ ] **Step 5: Add asymmetric twelve-column layouts and motion safeguards**

Use `.editorial-grid { display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); }`, explicit column spans, and mobile collapse at 760px. All reveal defaults must remain visible before JavaScript adds an enhancement class. The reduced-motion block sets transform/animation/transition to none and opacity to one.

- [ ] **Step 6: Run focused tests and commit**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: PASS.

```bash
git add components/site/hero.tsx components/site/intelligence-field.tsx components/site/brand-story.tsx components/site/process-narrative.tsx app/marketing.css app/editorial-redesign.test.ts app/page.tsx
git commit -m "feat: create Aritioz editorial narrative"
```

### Task 4: Add the project inquiry experience

**Files:**
- Create: `lib/project-inquiry.ts`
- Create: `lib/project-inquiry.test.ts`
- Create: `components/site/project-inquiry.tsx`
- Modify: `app/page.tsx`
- Modify: `app/marketing.css`

**Interfaces:**
- Produces: `type InquiryValues = { name: string; email: string; company: string; projectType: string; brief: string }`.
- Produces: `validateInquiry(values: InquiryValues): Partial<Record<keyof InquiryValues, string>>`.
- Produces: `buildInquiryMailto(values: InquiryValues): string`.
- Consumes: `[data-project-inquiry-trigger]` click events from Tasks 2 and 3.

- [ ] **Step 1: Write failing validation and handoff tests**

```ts
import { describe, expect, it } from 'vitest';
import { buildInquiryMailto, validateInquiry } from './project-inquiry';

const valid = { name: 'Anshuman', email: 'hello@example.com', company: 'Aritioz', projectType: 'AI product', brief: 'Build a launch workspace.' };

describe('project inquiry', () => {
  it('reports missing required fields and rejects spaced email input', () => {
    expect(validateInquiry({ ...valid, name: '', email: 'hello @example.com', brief: '  ' })).toEqual({
      name: 'Enter your name.',
      email: 'Enter a valid email address.',
      brief: 'Tell us a little about the project.',
    });
  });

  it('builds an encoded email handoff from trimmed values', () => {
    const url = buildInquiryMailto({ ...valid, name: ' Anshuman ' });
    expect(url).toMatch(/^mailto:/);
    expect(url).toContain('Anshuman');
    expect(url).toContain('AI%20product');
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run: `npm test -- lib/project-inquiry.test.ts`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement exact validation and mailto helpers**

Use `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` for the trimmed email, require trimmed `name`, `email`, and `brief`, and encode the subject/body with `URLSearchParams`. Use the project email already configured in the repository; if none exists, use `hello@aritioz.com` and keep it as a named constant `ARITIOZ_INQUIRY_EMAIL`.

- [ ] **Step 4: Build the accessible dialog and event bridge**

Use the existing Dialog primitive. Register one document click handler that detects `closest('[data-project-inquiry-trigger]')`, opens the dialog, and stores the trigger element for focus restoration. Render labels, inline `aria-describedby` errors, and a visible sentence explaining that submit opens the visitor's email app. On valid submit, set `window.location.href = buildInquiryMailto(values)`.

- [ ] **Step 5: Test and commit**

Run: `npm test -- lib/project-inquiry.test.ts app/editorial-redesign.test.ts`

Expected: PASS.

```bash
git add lib/project-inquiry.ts lib/project-inquiry.test.ts components/site/project-inquiry.tsx app/page.tsx app/marketing.css
git commit -m "feat: add accessible project inquiry flow"
```

### Task 5: Create non-repeating capability stories and showcase frame

**Files:**
- Create: `components/site/capabilities-editorial.tsx`
- Create: `components/site/product-showcase.tsx`
- Modify: `app/page.tsx`
- Modify: `app/marketing.css`
- Modify: `app/editorial-redesign.test.ts`

**Interfaces:**
- Produces: `CapabilitiesEditorial(): JSX.Element` with articles `capability--direction`, `capability--experience`, and `capability--intelligence`.
- Produces: `ProductShowcase(): JSX.Element` that embeds `<LaunchOSWorkspace />` under `id="work"`.
- Consumes: `LaunchOSWorkspace` from `components/launchos-workspace.tsx`.

- [ ] **Step 1: Add failing capability and showcase tests**

```ts
const capabilities = readFileSync(new URL('../components/site/capabilities-editorial.tsx', import.meta.url), 'utf8');
const showcase = readFileSync(new URL('../components/site/product-showcase.tsx', import.meta.url), 'utf8');

it('renders distinct capabilities and one embedded product workspace', () => {
  for (const title of ['Brand & Product Direction', 'Digital Experience', 'Applied Intelligence']) {
    expect(capabilities).toContain(title);
  }
  expect(showcase).toContain('id="work"');
  expect(showcase.match(/<LaunchOSWorkspace/g)?.length).toBe(1);
  expect(page).not.toContain('<DialogTrigger className="header-cta"');
});
```

- [ ] **Step 2: Run the test and verify failure**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: FAIL until the new section components are composed.

- [ ] **Step 3: Implement three composition-specific capability articles**

Use one text-led identity specimen, one interface-wireframe visual, and one SVG system map. Keep all service meaning as visible text; mark illustrative SVGs `aria-hidden="true"`. Do not map one shared card component over the three items.

- [ ] **Step 4: Implement the Seller Commerce OS case-study frame**

Add an editorial eyebrow, product title, qualitative outcome, three product-tour labels, and a browser frame around `LaunchOSWorkspace`. Product-tour controls scroll or focus the relevant visible workspace region; they must not duplicate or fake the workspace state.

- [ ] **Step 5: Add responsive capability and showcase styling**

Give every capability different grid spans on desktop. At 900px collapse the product intro above the browser frame. At 760px use a single column and remove nonessential depth layers. Use `overflow: clip` on the frame and avoid transform scaling that makes controls illegible.

- [ ] **Step 6: Test and commit**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: PASS.

```bash
git add components/site/capabilities-editorial.tsx components/site/product-showcase.tsx app/page.tsx app/marketing.css app/editorial-redesign.test.ts
git commit -m "feat: add capability stories and product showcase"
```

### Task 6: Redesign Seller Commerce OS while preserving AI behavior

**Files:**
- Modify: `components/launchos-workspace.tsx`
- Modify: `app/workspace.css`
- Create: `components/workspace-state.test.ts`
- Modify: `lib/chat-api.test.ts`

**Interfaces:**
- Preserves: `sendChatMessage(message, apiBase?, provider?, imageDataUrl?)` usage.
- Produces: `type WorkspaceMode = 'chat' | 'work'` and `type WorkspaceView = 'welcome' | 'conversation'` within the component.
- Produces: landmarks `.workspace-sidebar`, `.workspace-main`, `.workspace-composer`, `.workspace-workboard` used by Task 5's tour anchors.

- [ ] **Step 1: Add failing workspace structure and request-state tests**

```ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = readFileSync(new URL('./launchos-workspace.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../app/workspace.css', import.meta.url), 'utf8');

describe('Seller Commerce OS workspace', () => {
  it('preserves chat, attachment, history, and mode controls', () => {
    for (const contract of ['sendChatMessage', 'readImageFile', 'savedProjects', "'chat' | 'work'"]) {
      expect(source).toContain(contract);
    }
  });

  it('provides a real workboard and dismissible mobile navigation', () => {
    expect(source).toContain('workspace-workboard');
    expect(source).toContain('aria-label="Close workspace navigation"');
    expect(source).toContain('workspace-sidebar-backdrop');
  });

  it('prevents horizontal overflow and preserves tap targets', () => {
    expect(css).toContain('min-width: 0');
    expect(css).toContain('overflow-x: hidden');
    expect(css).toMatch(/min-height:\s*44px/);
  });
});
```

Add a `lib/chat-api.test.ts` case that verifies an empty server error body produces the existing safe fallback message instead of exposing response internals.

- [ ] **Step 2: Run tests and verify failure**

Run: `npm test -- components/workspace-state.test.ts lib/chat-api.test.ts`

Expected: FAIL because the redesigned landmarks and workboard are absent.

- [ ] **Step 3: Refactor the workspace into clear visual regions without changing transport logic**

Keep `submitPrompt`, `selectImage`, and `startNewProject` behavior. Add a compact product lockup, grouped sidebar navigation, active project treatment, backdrop button, and `X` close action. Add Escape handling for the mobile drawer and close it after project selection.

- [ ] **Step 4: Replace the empty state and upgrade the composer**

Render a welcome label, concise heading, short explanatory copy, and three starter prompt buttons. Replace the single-line prompt input with a textarea that submits on Enter and inserts a newline on Shift+Enter. Keep file input validation and expose loading/attachment errors through `aria-live`.

- [ ] **Step 5: Implement meaningful Work mode**

Render `.workspace-workboard` with a selected project summary, three status columns (`Ideas`, `In progress`, `Ready`), and static task examples sourced from the existing project names. Work mode must not call the AI endpoint and must retain the Chat mode conversation when users switch back.

- [ ] **Step 6: Style the workspace as a product, not a generic chat clone**

Use warm white canvas, charcoal navigation, electric cobalt active states, fine borders, and one restrained shadow. Keep body text at 14px or larger at showcase size. At 760px, make the sidebar a fixed drawer, show the backdrop, keep the composer controls at least 44px, and constrain the response measure to 68ch.

- [ ] **Step 7: Run workspace tests and commit**

Run: `npm test -- components/workspace-state.test.ts lib/chat-api.test.ts`

Expected: PASS.

```bash
git add components/launchos-workspace.tsx app/workspace.css components/workspace-state.test.ts lib/chat-api.test.ts
git commit -m "feat: redesign Seller Commerce OS workspace"
```

### Task 7: Add the closing conversion section and footer

**Files:**
- Create: `components/site/closing-cta.tsx`
- Create: `components/site/site-footer.tsx`
- Modify: `app/page.tsx`
- Modify: `app/marketing.css`
- Modify: `app/editorial-redesign.test.ts`

**Interfaces:**
- Produces: `ClosingCta(): JSX.Element` with `data-project-inquiry-trigger`.
- Produces: `SiteFooter(): JSX.Element` with working section anchors and current year.
- Consumes: inquiry event bridge from Task 4.

- [ ] **Step 1: Add failing closing-copy and footer tests**

```ts
const closing = readFileSync(new URL('../components/site/closing-cta.tsx', import.meta.url), 'utf8');
const footer = readFileSync(new URL('../components/site/site-footer.tsx', import.meta.url), 'utf8');

it('closes with the approved conversion statement and complete footer navigation', () => {
  expect(closing).toContain('Ready to turn an idea into a business?');
  expect(footer).toContain('Creative intelligence for what comes next.');
  expect(footer).toContain('new Date().getFullYear()');
});
```

- [ ] **Step 2: Run the test and verify failure**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: FAIL until both components are wired into `page.tsx`.

- [ ] **Step 3: Implement the cinematic CTA and restrained footer**

Use the existing `aritiouz-cinematic-overlay.png` as an art-directed background crop with a solid-color fallback. Keep the CTA copy and button as real HTML over the image. Footer anchors point to existing IDs and the year is rendered server-side.

- [ ] **Step 4: Add responsive styling and reduced-motion behavior**

Use oversized but clamped CTA type, keep text contrast above 4.5:1, and disable the background drift in the existing reduced-motion media query.

- [ ] **Step 5: Test and commit**

Run: `npm test -- app/editorial-redesign.test.ts`

Expected: PASS.

```bash
git add components/site/closing-cta.tsx components/site/site-footer.tsx app/page.tsx app/marketing.css app/editorial-redesign.test.ts
git commit -m "feat: finish Aritioz conversion journey"
```

### Task 8: Verify production quality across the complete experience

**Files:**
- Modify only if verification exposes a defect: files owned by Tasks 1–7

**Interfaces:**
- Consumes: the complete marketing page, inquiry dialog, and workspace.
- Produces: a clean build and documented manual verification in the final handoff.

- [ ] **Step 1: Run the complete automated suite**

Run: `npm test`

Expected: all tests PASS.

- [ ] **Step 2: Run lint and fix only errors introduced by this redesign**

Run: `npm run lint`

Expected: exit code 0. Preserve unrelated user changes if pre-existing diagnostics appear.

- [ ] **Step 3: Run the production build**

Run: `npm run build:vps`

Expected: exit code 0 with no missing import, type, or route error.

- [ ] **Step 4: Verify desktop and mobile browser behavior**

Run the local site and inspect at 1440×900, 1024×768, 768×1024, and 390×844. Confirm: no horizontal overflow; sticky navigation and all anchors work; hero text remains readable without canvas; mobile navigation and workspace drawer open/close; every CTA opens inquiry; invalid inquiry fields announce errors; Explore our work reaches the product; Chat/Work switching retains the conversation; attachment controls remain operable; reduced motion removes continuous movement.

- [ ] **Step 5: Verify keyboard and console quality**

Tab from the skip link through navigation, process controls, product tour, workspace, inquiry, and footer. Confirm visible focus, sensible order, Escape dismissal, focus restoration, and no browser console errors.

- [ ] **Step 6: Commit verification fixes if any**

```bash
git add app components lib
git commit -m "fix: polish Aritioz responsive experience"
```

If no fixes were needed, do not create an empty commit.
