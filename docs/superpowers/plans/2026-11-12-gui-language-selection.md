# GUI Language Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an extensible French/English/Danish language selector in GUI preferences, with country flags, persistent choice, and immediate application.

**Architecture:** A small `ui/i18n.py` module owns supported-language metadata and Python-string catalogues; UI code uses a translation lookup keyed by stable source strings. The preference dialog receives the current language, displays native language names with flags, and the main window rebuilds its translated interface after acceptance while preserving current conversion preferences and source/results state.

**Tech Stack:** Python standard library, PyQt5/PyQt6 compatibility layer, `unittest`, `QSettings`.

**Spec:** `docs/superpowers/specs/2026-11-12-gui-language-selection-design.md`

## Global Constraints

- Support PyQt5/PyQt6 and AppImage packaging.
- Translate GUI strings; do not change the CLI or conversion engine.
- Include Français, English and Dansk, shown with country flags and native language names.
- Persist selected language in `QSettings`; use French for missing/invalid preference.
- Apply the selected language when preferences are accepted.
- Add future languages through catalogues without changing selection/persistence logic.
- Add no external translation dependency.

## Review Focus

- Missing/invalid saved language must fall back to French (test language resolution and window startup).
- Accepted language selection must persist and immediately update visible GUI (test preference acceptance and translated labels).
- Cancelled preference changes must not update or persist language (test dialog rejection).
- Switching languages while sources/results exist must preserve them and conversion preferences (test retranslation preserves window state).
- PyQt5/PyQt6 and frozen packaging must continue to import the translation module (run compatibility tests and update/check PyInstaller hidden imports).

---

### Task 1: Translation catalogues and language metadata

**Files:**
- Create: `ui/i18n.py`
- Modify: `test_gui_qt.py`

**Interfaces:**
- Produces `LANGUAGES`, ordered records with stable locale code, native name and country flag, and `translate(language: str, text: str) -> str`.
- Catalogues include all GUI text introduced by existing `gui_qt.py`, `ui/options.py`, `ui/source_tree.py` and `ui/result_tree.py`; unknown language/text safely returns source text or French fallback.

- [ ] Write tests for supported ordering/native names/flags, representative translations for all three locales, unknown text fallback and invalid-locale fallback.
- [ ] Run `python3 -m unittest test_gui_qt` and confirm the new tests fail before implementation.
- [ ] Implement metadata and per-language catalogues in `ui/i18n.py`; use stable English source strings for lookup while retaining French as initial default via explicit catalogues.
- [ ] Run `python3 -m unittest test_gui_qt` and confirm the catalogue tests pass.

### Task 2: Preferences selector and immediate GUI translation

**Files:**
- Modify: `ui/options.py`
- Modify: `gui_qt.py`
- Modify: `ui/source_tree.py`
- Modify: `ui/result_tree.py`
- Modify: `test_gui_qt.py`

**Interfaces:**
- `PreferencesDialog(..., language: str, parent=None)` exposes `language_combo`; each item stores locale code, displays flag and native language name.
- `ConvertisseurQt` owns the current language and a single retranslation path used at startup and after preference acceptance.

- [ ] Add tests proving the selector appears first, stores/selects `fr`, `en`, `da`, and cancellation preserves language.
- [ ] Add tests proving startup restores persisted language, invalid/missing preference selects French, and acceptance persists and immediately translates main and preferences UI.
- [ ] Add tests proving retranslation preserves conversion options and already-added tree entries; verify visible status/result/source strings use the active catalogue.
- [ ] Run targeted tests and confirm they fail before implementing UI wiring.
- [ ] Add language row at the beginning of preferences; pass language through `QSettings`, apply translated labels, actions, tooltips, file/folder dialogs, status/error messages, and existing source/result tree status strings.
- [ ] Implement retranslation so changing locale updates existing widgets without discarding source/results, conversion settings, or selected output path.
- [ ] Run `python3 -m unittest test_gui_qt` and confirm all GUI tests pass.

### Task 3: Packaging and regression verification

**Files:**
- Modify: `.github/workflows/build-appimage.yml`
- Modify: `test_gui_qt.py` only if needed for packaging/import regression.

**Interfaces:**
- PyInstaller explicitly includes `ui.i18n` following existing hidden-import conventions.

- [ ] Add a packaging/import check that the translation catalogue is importable and all language values are available without Qt Linguist resources.
- [ ] Add `--hidden-import ui.i18n` to the AppImage build command.
- [ ] Run `python3 -m unittest` and `python3 -m py_compile gui_qt.py ui/*.py`.
- [ ] Confirm the PyInstaller command includes the new module; run the AppImage workflow only if its external build tools are available locally.
