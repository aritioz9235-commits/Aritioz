# Aritioz Project Workspace Redesign

## Purpose

Replace the existing Seller Commerce OS presentation shown by the landing page's
**Start a project** action with an Aritioz-branded workspace that closely follows
the supplied ChatGPT-style reference: calm white canvas, persistent sidebar,
compact top controls, and a centered prompt composer. The workspace remains an
Aritioz product and preserves the existing chat API and image attachment flow.

## Scope and Success Criteria

- Opening **Start a project** shows the redesigned Aritioz workspace.
- The desktop view includes the reference's key regions: sidebar, Chat/Work
  switcher, header utilities, empty prompt state, composer, shortcuts, and
  account area.
- Aritioz replaces ChatGPT as the visible product name. The copy and controls
  do not claim to be ChatGPT or expose OpenAI-specific product areas.
- Sending a non-empty prompt retains the current request/response behavior and
  displays an Aritioz conversation state.
- Image upload, attachment feedback, New chat reset, Work mode, keyboard
  controls, and the responsive mobile navigation remain functional.
- The result renders cleanly at desktop and mobile sizes without horizontal
  overflow.

## Visual Direction

The workspace uses an almost-white canvas, black primary text, muted gray
secondary text, fine #ededed rules, and one restrained cobalt-blue accent.
Controls are subtly rounded rather than glassy. Shadows are soft and limited to
the composer and selected controls. Lucide icons continue to provide all UI
glyphs. The identity is an Aritioz wordmark plus a compact sparkle mark.

## Layout

`LaunchOSWorkspace` remains the single interactive client component rendered in
the existing Start a project dialog. Its internal layout is rebuilt as follows:

### Sidebar

The fixed left rail contains the **Aritioz** wordmark at its upper-left edge
(directly replacing the reference screenshot's “ChatGPT” label), search/sidebar
controls, a selected **New chat** action, and the navigation items Images, Library,
Scheduled, Plugins, Projects, Codex, and More. A profile block and Upgrade
action anchor the bottom. Existing saved/recent project data remains available
under the Projects area rather than competing with the reference's primary
navigation.

### Main Header

The center top bar holds accessible **Chat** and **Work** tabs. The right edge
contains a Compare plans action and a non-destructive utility control. Tabs use
real button state and `aria-selected`; Work mode changes the canvas heading and
starter context rather than being purely decorative.

### Empty Canvas and Composer

With no submitted prompt, the canvas centers the heading “What’s on the agenda
today?” and a full-width rounded composer. The composer provides image
attachment, typed prompt input, a Think affordance, voice-input placeholder,
and enabled/disabled send button. Beneath it are actionable starter prompts for
image creation, writing/editing, and web research. Selecting a starter action
prefills the existing input.

### Conversation State

After submission, the canvas replaces the empty heading with the submitted
prompt and the API's Aritioz response. Loading, API error, provider/model
metadata, image attachment preview, and New chat reset remain explicit and
accessible.

## Responsive and Accessibility Behavior

At narrow widths, the sidebar is hidden behind the existing menu control and
opens as a dismissible overlay; the content remains single-column. Header
utilities collapse before the composer does, and controls retain accessible
names and visible focus states. Motion remains limited to short color,
background, and transform transitions, and is removed under reduced-motion
preferences.

## Files and Tests

- `components/launchos-workspace.tsx`: component markup, interactions, labels,
  and state wiring.
- `app/globals.css`: scoped workspace styling and responsive rules.
- A focused component test: verifies Aritioz empty-state content and a starter
  action/prompt interaction before behavior is implemented.
- Existing test suite, linter, production build, and browser check verify the
  integration.

## Boundaries

This is a visual and interaction redesign of the existing project workspace.
It does not add account management, billing, actual speech recognition, web
search, or image generation services. Those visible controls are affordances
or prompt starters unless the existing backend already supports the requested
operation.
