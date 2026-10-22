# AGENTS.md

## Runtime and entrypoints

- This is a small, single-application Python project. `core.py` contains shared conversion options, file discovery, FFmpeg helpers, conversion execution, and structured results; `m4a2mp3.py` is the CLI entrypoint, `gui_qt.py` is the GUI entrypoint, and Qt components are under `ui/`.
- The CLI uses only the Python standard library, but both interfaces require the external `ffmpeg` executable to be installed and available on `PATH`. The GUI also requires PyQt6 or PyQt5; `ui/qt_compat.py` tries PyQt6 first, then PyQt5.
- Launch the GUI with `python3 gui_qt.py`. The CLI currently expects `python3 m4a2mp3.py --dossier <directory>`; although `--dossier` is not marked required by argparse, omitting it causes an error when the program checks the directory. The examples in `README.md` currently pass the directory positionally and do not match the parser; keep the parser and documentation aligned when either is changed.
- Both conversion and GUI cover-art extraction call FFmpeg as a subprocess. In frozen PyInstaller builds, use `core.ffmpeg_environment()` for every FFmpeg subprocess: it restores `LD_LIBRARY_PATH_ORIG` (or removes the bundle-specific `LD_LIBRARY_PATH`) so system FFmpeg does not load incompatible libraries bundled with the application.
- Conversion writes a temporary MP3 beside its source and atomically replaces the destination on success. Keep CLI and GUI conversion behavior aligned by calling `core.convert_file`; overwriting existing MP3 files is enabled by default.

## Build and verification

- The AppImage workflow is `.github/workflows/build-appimage.yml`. It builds on Ubuntu 22.04 with Python 3.11, installs PyInstaller and PyQt6, and packages `gui_qt.py` with explicit hidden imports for `core` and `ui` modules. FFmpeg is not bundled: it must be installed on the target system and found on `PATH`. Update the hidden-import list when adding UI modules, and keep `AppRun` and desktop/icon assets in sync with packaging changes.
- The repository has no checked-in test, lint, formatter, or type-check configuration. Do not assume such a command exists; verify changes with relevant entrypoints and, for packaging changes, the AppImage workflow. GUI execution and conversion tests require PyQt and FFmpeg respectively.