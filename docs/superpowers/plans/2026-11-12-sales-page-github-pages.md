# Sales Page and GitHub Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a factual, responsive FR/EN/DA product page in this repository and deploy it automatically to GitHub Pages.

**Architecture:** A dependency-free static site lives under `docs/`, with semantic HTML, CSS, and a small JavaScript language switcher. A GitHub Actions workflow publishes `docs/` on pushes to `main` and supports manual dispatch.

**Tech Stack:** HTML, CSS, vanilla JavaScript, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-12-sales-page-design.md`

## Global Constraints

- Supported audio input: `.m4a`, `.wav`, `.aiff`, `.aif`.
- FFmpeg must be installed and available on PATH for conversion.
- AppImage builds are Linux x86_64 and published on version-tag GitHub Releases.
- Do not claim unavailable platform binaries, testimonials, performance numbers, or prices.
- The temporary interface illustration must be clearly marked and straightforward to replace with a user screenshot.
- Visual direction: album-cover publishing, with deep blue-black ink, warm paper, vermilion accents, and editorial music-release typography; keep actual links and copy functional and legible.
- No runtime dependency or framework; default language French with English and Danish available.

## Review Focus

- Page opened below a GitHub Pages project base path: use only relative asset links and ensure links work under both project pages and local serving.
- Language changes with keyboard and updates document language/title and stored preference; test each language and saved preference.
- Long translations on narrow screens: inspect the 390px layout for overflow and clipped controls.
- AppImage link points to the repository Releases rather than inventing a release tag or binary URL; test links against the existing workflow facts.
- Deployment permissions/environment: workflow grants Pages deployment permissions and uses the official Pages artifact/deploy actions.

---

### Task 1: Add the static trilingual landing page

**Files:**
- Create: `PRODUCT.md`
- Create: `docs/index.html`
- Create: `docs/assets/site.css`
- Create: `docs/assets/site.js`
- Create: `docs/assets/interface-placeholder.svg`
- Create: `.impeccable/surfaces/docs-index.md`

**Interfaces:**
- The HTML provides a `data-i18n` keyed content surface and language selector with `fr`, `en`, and `da` values.
- `docs/assets/site.js` owns translation dictionaries and initializes the document from the saved language or French.

- [ ] **Step 1: Add content validation checks**

Create a Python `unittest` test that parses the site source and asserts all three language dictionaries cover the same keys, supported source formats and FFmpeg requirement are stated in every language, primary AppImage and repository links exist, and the image placeholder has explicit replacement guidance.

- [ ] **Step 2: Run the check to confirm it fails before the page exists**

Run: `python3 -m unittest test_sales_page -v`
Expected: FAIL because the landing page assets are missing.

- [ ] **Step 3: Add confirmed product context and build the page**

Build `docs/index.html`, `site.css`, `site.js`, and `interface-placeholder.svg` in the approved album-cover publishing direction; provide accurate FR/EN/DA translations, accessible language buttons, responsive layout, and links to the existing GitHub Releases and repository. Use relative asset paths. Record the direction contract in `.impeccable/surfaces/docs-index.md` using the approved surface design.

- [ ] **Step 4: Run the checks**

Run: `python3 -m unittest test_sales_page -v`
Expected: PASS for translation parity, factual feature coverage, links, and placeholder instructions.

### Task 2: Configure automatic GitHub Pages publication

**Files:**
- Create: `.github/workflows/deploy-pages.yml`

**Interfaces:**
- Deploy from the repository's `docs/` directory using GitHub Pages artifact upload and deployment actions.

- [ ] **Step 1: Add the Pages workflow**

Trigger on pushes to `main` and `workflow_dispatch`; grant `contents: read`, `pages: write`, and `id-token: write`; configure Pages; upload `docs/` as the artifact; deploy it to the Pages environment. Do not alter the existing AppImage workflow.

- [ ] **Step 2: Validate workflow and run repository tests**

Run: `python3 -m unittest discover -v`
Expected: all existing and new tests pass. Check the workflow YAML structure and inspect changed files for external build dependencies.

### Task 3: Verify local preview and responsive behavior

**Files:**
- Modify only if verification reveals issues in `docs/index.html`, `docs/assets/site.css`, or `docs/assets/site.js`.

- [ ] **Step 1: Start local preview**

Run from repository root: `python3 -m http.server 8000 --directory docs`
Expected: site is served at `http://localhost:8000` and assets load.

- [ ] **Step 2: Verify language interaction and responsive layout**

Use a browser at desktop and 390px width; verify selector, persistence, accessible focus states, no horizontal overflow, and correct links in all languages. Stop the server after verification.

- [ ] **Step 3: Run final project verification**

Run: `python3 -m unittest discover -v` and `python3 -m compileall -q core.py m4a2mp3.py gui_qt.py`.
Expected: tests pass and Python compilation succeeds; no lint/type-check configuration exists per `AGENTS.md`.
