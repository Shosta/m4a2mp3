# Site Screenshot Carousel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the site's placeholder hero visual with an accessible carousel of the three app screenshots.

**Architecture:** Keep the current HTML/CSS/JS architecture and avoid dependencies. Add carousel markup and styles in the existing files, with a small native JavaScript controller for timed rotation and manual controls.

**Tech Stack:** HTML, CSS, vanilla JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-24-site-screenshot-carousel-design.md`

## Global Constraints

- No external dependencies or unrelated design changes.
- Automatic advance every 5 seconds; manual previous/next and slide selection.
- Pause while pointer-hovered or keyboard-focused; do not auto-rotate with `prefers-reduced-motion: reduce`.
- Keep carousel content understandable with keyboard and screen reader.

## Review Focus

- Reduced-motion preference: autoplay does not start.
- Keyboard focus or pointer hover: autoplay pauses and resumes after interaction leaves.
- Manual navigation at either end: wraps between the three screenshots.
- Language selection: existing page translations continue to work.
- JavaScript disabled: first real screenshot remains visible.

---

### Task 1: Replace hero placeholder with screenshot carousel

**Files:**
- Modify: `docs/index.html` — replace `.sleeve-frame` placeholder with three slides and accessible controls.
- Modify: `docs/assets/site.css` — preserve existing sleeve styling, add slide/control styling and responsive behavior.
- Modify: `docs/assets/site.js` — add initialization for previous/next, indicators, and 5-second rotation; pause on hover/focus and respect reduced motion.

**Interfaces:**
- Consumes: existing translation mechanism (`data-i18n`, `translations`, `applyLanguage`).
- Produces: carousel root `[data-carousel]`, buttons `[data-carousel-previous]`, `[data-carousel-next]`, and indicators `[data-carousel-slide]` with `aria-label` and `aria-current` updates.

- [ ] **Step 1: Update `docs/index.html`** with the three assets in order (`m4a2mp3 - 1.png`, `- 2.png`, `- 3.png`); include meaningful image alt text, previous/next buttons and three slide-selection buttons. Keep the first image visible by default.
- [ ] **Step 2: Add carousel styles in `docs/assets/site.css`** so slides share the current frame, only the active slide is shown, controls match the existing palette, and narrow layouts remain usable.
- [ ] **Step 3: Add carousel controller in `docs/assets/site.js`** to support wrapping manual navigation, indicator updates, 5-second automatic advance, hover/focus pause, and no autoplay for reduced motion. Initialize safely when the carousel is present.
- [ ] **Step 4: Verify static markup and script syntax** with `git diff --check` and `node --check docs/assets/site.js`; confirm image files exist at the referenced paths.
- [ ] **Step 5: Run local preview** using `python3 -m http.server --directory docs 8000`, then check the hero, all manual controls, timed advance, pause/resume, keyboard access, and responsive layout in a browser.
