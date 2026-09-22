# Aritioz Editorial Redesign

## Purpose

Redesign the existing Aritioz landing page into a premium creative intelligence studio experience while preserving the brand statement, core content, existing visual assets, and Seller Commerce OS functionality.

The page must communicate that Aritioz combines strategy, design, and applied AI to turn ambitious ideas into useful digital products. It should feel authored and editorial rather than assembled from common SaaS patterns.

## Creative Direction

The selected direction is **Editorial Signal**: Swiss editorial structure, luxury-brand restraint, and subtle technological details.

- Warm off-white and deep near-black form the primary contrast.
- Muted graphite supports secondary information.
- Electric cobalt is the single distinctive accent.
- Display typography carries the expressive moments; a modern sans-serif supports readable interface and body copy.
- Fine rules, precise labels, generous whitespace, and asymmetrical alignment establish the system.
- Gradients, glow, glass, and rounded cards appear only when necessary for the product interface, not as the page's default visual language.

## Page Architecture

### Navigation

A minimal sticky header contains the Aritioz wordmark, links to Story, Process, Capabilities, and Work, plus a prominent Start a project action. The mobile version uses an accessible disclosure menu with keyboard support and clear focus states.

Start a project opens an on-site inquiry dialog. Explore our work scrolls directly to the featured Seller Commerce OS section.

### Hero

The hero occupies the opening viewport and makes “Where ideas become intelligent.” the dominant statement. Supporting copy positions Aritioz as “Creative intelligence for what comes next.” The primary and secondary actions remain visible without competing with the headline.

A lightweight generative field of points, lines, and grid fragments responds gently to pointer movement. It runs entirely in the browser, avoids continuous React state updates, scales down on smaller screens, and becomes static when reduced motion is requested. The opening sequence uses short staggered reveals and never delays access to content.

### Brand Story

The Aritioz definition becomes an editorial manifesto rather than a conventional centered section. Large typographic fragments, phonetic detail, and concise prose span an asymmetric twelve-column composition. Existing language about imagination meeting intelligence remains the narrative core.

### Process

Discover, Design, and Deliver form a connected three-step narrative. On larger screens, selecting or focusing a step updates a shared visual field and supporting statement. On touch and small screens, the same content becomes a clear vertical sequence with no interaction required to understand it. Strong numbering and a continuous rule visually connect the stages.

### Capabilities

The three capabilities use deliberately different compositions instead of repeated cards:

- **Brand & Product Direction** pairs concise strategy copy with a typographic identity study.
- **Digital Experience** uses a structured interface/window composition that demonstrates design systems and interaction craft.
- **Applied Intelligence** uses an abstract system map to show useful AI and automation without robot imagery.

Each capability includes a short description and precise service labels. Decorative visuals remain accessible-hidden while meaningful content remains in semantic text.

### Featured Product

Seller Commerce OS appears as a dedicated case-study section and the primary proof of work. A premium browser/device frame contains the existing functional workspace UI. Surrounding editorial content explains the product intent and core areas without inventing metrics.

A small product-tour control lets visitors move among three representative views. The interface stays readable, is fully keyboard-operable, and becomes a straightforward stacked presentation on mobile. The workspace is embedded within this section; it no longer appears as an accidental consequence of the global Start a project action.

### Seller Commerce OS Interface

The workspace shown in the supplied screenshot will be visually redesigned without removing its chat, image attachment, mode switching, saved-project selection, or backend response behavior.

- The product receives its own identity lockup and a compact contextual top bar so it reads as a real Aritioz product rather than a generic chat clone.
- The sidebar becomes narrower and more structured, with a clear New project action, grouped navigation, compact project history, an active state, and a quieter account area. On mobile it behaves as an accessible dismissible drawer with a backdrop.
- The empty center canvas gains an editorial welcome block, a short explanation of what the workspace can do, and a small set of useful starter actions. This removes the excessive dead space visible in the current interface.
- The composer becomes a deliberate working surface with stronger contrast, a multiline input, attachment preview, selected working mode, and an unambiguous send state.
- The Chat and Work modes have meaningful visual and content differences. Work mode presents an organized project view rather than only changing the headline.
- Submitted prompts and generated answers use a readable conversation layout with clear authorship, status, error feedback, and response metadata.
- The interface uses warm neutral surfaces, graphite text, and the same electric cobalt accent as the marketing site. Borders, radii, shadows, and icon sizes follow a small token set instead of appearing ad hoc.
- At showcase scale, the workspace preserves readable type and controls; it does not shrink a desktop UI until the content becomes decorative or illegible.

### Final CTA

The closing section centers on “Ready to turn an idea into a business?” with a cinematic but restrained composition: oversized typography, a shifting crop of existing Aritioz imagery, and one high-value Start a project action. Motion is subtle and disabled for reduced-motion users.

### Footer

The footer contains the Aritioz identity, “Creative intelligence for what comes next,” section navigation, and the current year. It uses the same editorial grid and avoids unnecessary social or partner claims.

## Inquiry Flow

Start a project opens a focused accessible dialog containing name, email, company, project type, and a short project brief. The initial implementation validates required fields client-side and presents a clear submission state. Because no production form endpoint is currently specified, submission uses an explicit email handoff rather than pretending data has been stored. This boundary is visible in the interface and can later be replaced by a real endpoint without redesigning the form.

The dialog traps focus, closes with Escape, restores focus to its trigger, exposes validation messages to assistive technology, and remains usable at mobile viewport heights.

## Component Structure

The landing page will be separated into focused components:

- `SiteHeader` and mobile navigation
- `Hero` and `IntelligenceField`
- `BrandStory`
- `ProcessNarrative`
- `CapabilitiesEditorial`
- `ProductShowcase`
- `ProjectInquiry`
- `ClosingCta`
- `SiteFooter`

Content that benefits from reuse will live in typed data structures rather than repeated markup. Existing UI primitives and Seller Commerce OS logic remain in place where they serve the design. No new runtime dependency is required for motion or the generative field.

## Responsive Behavior

The desktop layout uses a twelve-column grid with a shared maximum width and consistent page gutters. Tablet compositions reduce column spans while preserving asymmetry. Mobile uses a single reading column, comfortable tap targets, simplified decorative layers, and a compact navigation menu. Typography uses fluid clamps with conservative maximums to avoid clipping and horizontal overflow.

## Motion and Interaction

Motion is implemented with CSS transitions, Intersection Observer, and a lightweight canvas or SVG field. Reveals are brief and occur once. Hover effects always have equivalent focus behavior. Scroll-linked effects use transforms only and remain restrained. `prefers-reduced-motion` disables parallax, pointer response, and staggered transitions while preserving all content.

## Accessibility and Semantics

- One `h1`, followed by a logical heading hierarchy.
- Semantic `header`, `nav`, `main`, `section`, `article`, and `footer` landmarks.
- Skip link and visible `:focus-visible` treatment.
- WCAG AA text contrast across both light and dark sections.
- All controls receive accessible names and keyboard behavior.
- Decorative imagery is hidden from assistive technology; informative images receive useful alt text.
- No important content depends on animation, hover, color, or canvas rendering.

## Metadata and Performance

Metadata will describe Aritioz as a creative intelligence studio and reuse the existing favicon. Existing raster assets will be served at appropriate sizes and loading priorities. Below-the-fold images use lazy loading. The interactive visual avoids external libraries and adapts its rendering density to device size and pixel ratio.

The production build must complete without errors. The final verification covers linting, tests, responsive layouts, keyboard interaction, reduced motion, internal anchor behavior, dialog behavior, and browser console errors.

## Success Criteria

- The first viewport clearly communicates Aritioz's positioning and offers two unambiguous actions.
- The site feels bespoke, editorial, and technologically credible rather than like a generic AI template.
- The Seller Commerce OS reads as featured work and remains functionally usable.
- Start a project opens a dedicated inquiry experience, not the product workspace.
- The page is polished and usable across desktop, tablet, and mobile.
- Accessibility, performance, and reduced-motion behavior are part of the finished experience rather than follow-up work.
