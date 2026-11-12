# Language Dropdown Implementation Plan

> **For agentic workers:** Execute this concise plan inline. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Replace the three-letter language buttons with a native dropdown showing flag and language name.

**Architecture:** Use a single native `<select>` with three localized options and update the existing translation initializer/event handling to select the current language.

**Tech Stack:** HTML, CSS, vanilla JavaScript, Python unittest/Chromium.

**Spec:** `docs/superpowers/specs/2026-11-12-language-dropdown-design.md`

## Global Constraints

- Language choices: 🇫🇷 Français, 🇬🇧 English, 🇩🇰 Dansk.
- Preserve French default, stored language preference, translated labels, title, description, and document `lang`.
- Keep assets and runtime dependency-free; preserve responsive masthead.

## Review Focus

- Unsupported saved language: falls back to French and selects the French option.
- Native menu labels and selected state: correctly correspond to all three language codes.
- Keyboard selection: changing `<select>` updates the whole page and persists through reload.
- Narrow masthead: dropdown fits alongside the wordmark at 390px without horizontal scrolling.

---

### Task: Implement and verify dropdown

**Files:**
- Modify: `docs/index.html`
- Modify: `docs/assets/site.css`
- Modify: `docs/assets/site.js`
- Modify: `test_sales_page.py`

- [ ] Add failing tests for three flag/name options, initial selection, language change, persistence, and no mobile overflow.
- [ ] Run the targeted test and confirm it fails against the current buttons.
- [ ] Replace the buttons with a labeled native select; update its selected value in `applyLanguage` and listen to `change`.
- [ ] Run targeted and full Python tests, compileall, and inspect desktop/mobile Chromium screenshots.
