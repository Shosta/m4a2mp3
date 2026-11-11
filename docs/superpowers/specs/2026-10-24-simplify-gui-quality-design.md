# Simplify GUI Audio Quality Choices — Design

## Intent

Make the Qt converter's quality choice understandable without requiring users to interpret ten numbered LAME VBR settings.

## Goals and non-goals

- Replace the GUI's ten quality labels with three clear options: `Économique`, `Équilibrée`, and `Haute qualité`.
- Map them to existing FFmpeg/LAME VBR values `7`, `4`, and `0`, respectively.
- Keep `Haute qualité` selected by default to preserve current behavior.
- Keep the change UI-only: do not alter core conversion semantics, CLI options, or the default in `core.py`.
- Explain the quality/file-size trade-off in concise helper text.

## Approaches

- **UI-only mapping (chosen):** map three visible options onto existing VBR values in the Qt component. This keeps the agreed scope small and preserves the core/CLI interfaces.
- **Named presets in core and CLI:** centralize named tiers across all interfaces, but expands scope and changes CLI behavior beyond this request.

The UI-only mapping was chosen to solve the user's immediate discoverability issue without affecting the established core and command-line behavior.

## Constraints and decisions

- Modify `ui/options.py` only, except for focused tests if needed.
- Preserve the `ConversionOptions.quality` property contract: it returns a string accepted by the existing FFmpeg `-q:a` argument.
- Keep the default at `q=0` (`Haute qualité`).
- Avoid claiming exact bitrates; file size and perceived quality depend on source audio.

## Remaining implementation decisions

- Select the default by matching the quality value rather than depending on a positional index.
- Verify all three choices return their intended VBR strings and the default is `0`.
- Verify the GUI still initializes with supported Qt bindings; no core/CLI changes are in scope.
