import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


DEFAULT_QUALITY = "0"
DEFAULT_JOBS = 4
MIN_JOBS = 1
MAX_JOBS = 6
DEFAULT_DELETE_SOURCES = False
DEFAULT_OVERWRITE = True
SUPPORTED_AUDIO_EXTENSIONS = frozenset({".m4a", ".wav", ".aiff", ".aif"})
WINDOWS_RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
    | {f"COM{number}" for number in "¹²³"}
    | {f"LPT{number}" for number in "¹²³"}
)


def normalized_path_key(path: Path | str) -> str:
    return os.path.normpath(str(path)).casefold()


class ConversionStatus(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class ConversionOptions:
    quality: str = DEFAULT_QUALITY
    jobs: int = DEFAULT_JOBS
    delete_sources: bool = DEFAULT_DELETE_SOURCES
    overwrite: bool = DEFAULT_OVERWRITE


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    status: ConversionStatus
    message: str

    @property
    def succeeded(self) -> bool:
        return self.status is not ConversionStatus.ERROR


def ffmpeg_environment() -> dict[str, str]:
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        original_library_path = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if original_library_path is None:
            env.pop("LD_LIBRARY_PATH", None)
        else:
            env["LD_LIBRARY_PATH"] = original_library_path
    return env


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def is_supported_audio(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        and not path.name.startswith("._")
    )


def is_m4a(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".m4a" and not path.name.startswith("._")


def _discover_files(
    directory: Path,
    predicate: Callable[[Path], bool],
    on_error: Optional[Callable[[Path, OSError], None]],
) -> list[Path]:
    files = []
    try:
        candidates = directory.rglob("*")
        for candidate in candidates:
            try:
                if predicate(candidate):
                    files.append(candidate)
            except OSError as exc:
                if on_error is None:
                    raise
                on_error(candidate, exc)
    except OSError as exc:
        if on_error is None:
            raise
        on_error(directory, exc)
    return sorted(files)


def discover_audio(
    directory: Path,
    on_error: Optional[Callable[[Path, OSError], None]] = None,
) -> list[Path]:
    return _discover_files(directory, is_supported_audio, on_error)


def discover_m4a(
    directory: Path,
    on_error: Optional[Callable[[Path, OSError], None]] = None,
) -> list[Path]:
    return _discover_files(directory, is_m4a, on_error)


def _tag_value(tags: object, name: str) -> str:
    if not isinstance(tags, dict):
        return ""
    for key, value in tags.items():
        if isinstance(key, str) and key.casefold() == name.casefold():
            return value.strip() if isinstance(value, str) else ""
    return ""


def read_audio_tags(source: Path) -> tuple[str, str]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_format", "-show_streams",
                "-of", "json", str(source),
            ],
            capture_output=True,
            text=True,
            env=ffmpeg_environment(),
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("ffprobe timed out") from exc
    if result.returncode != 0:
        raise ValueError(f"ffprobe failed: {result.stderr.strip()}")
    try:
        probe_data = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("ffprobe returned invalid JSON") from exc
    if not isinstance(probe_data, dict):
        raise ValueError("ffprobe returned invalid data")

    format_data = probe_data.get("format")
    format_tags = format_data.get("tags") if isinstance(format_data, dict) else None
    streams = probe_data.get("streams", [])
    if not isinstance(streams, list):
        raise ValueError("ffprobe returned invalid streams")
    audio_tags = next(
        (
            stream.get("tags")
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "audio"
        ),
        None,
    )
    artist = _tag_value(format_tags, "artist") or _tag_value(audio_tags, "artist") or "Artiste inconnu"
    album = _tag_value(format_tags, "album") or _tag_value(audio_tags, "album") or "Album inconnu"
    return artist, album


def _safe_path_component(value: str, fallback: str) -> str:
    component = value.strip()
    component = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", component)
    component = component.strip(" .")
    if component in {"", ".", ".."}:
        return fallback
    if component.split(".", 1)[0].rstrip(" .").upper() in WINDOWS_RESERVED_DEVICE_NAMES:
        component = f"_{component}"
    return component


def output_path_from_tags(source: Path, output_root: Path, artist: str, album: str) -> Path:
    root = output_root.resolve()
    artist_component = _safe_path_component(artist, "Artiste inconnu")
    album_component = _safe_path_component(album, "Album inconnu")
    destination = root / artist_component / album_component / source.with_suffix(".mp3").name
    resolved_destination = destination.resolve()
    if not resolved_destination.is_relative_to(root):
        raise ValueError("Generated destination escapes output root")
    return destination


def output_path_for(sources: list[Path]) -> dict[Path, Path]:
    destinations = {}
    groups = {}
    for source in sources:
        destination = source.with_suffix(".mp3")
        groups.setdefault(normalized_path_key(destination), (destination, []))[1].append(source)
    for destination, colliding_sources in groups.values():
        if len(colliding_sources) == 1:
            destinations[colliding_sources[0]] = destination
        else:
            for source in colliding_sources:
                destinations[source] = source.with_name(f"{source.name}.mp3")
    return destinations


def convert_file(
    source: Path,
    options: ConversionOptions,
    destination: Optional[Path] = None,
) -> ConversionResult:
    destination = source.with_suffix(".mp3") if destination is None else destination
    if destination.exists() and not options.overwrite:
        return ConversionResult(source, ConversionStatus.SKIPPED, "ignoré (mp3 déjà présent)")

    temporary_path = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".mp3", delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)

        command = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(source),
            "-map", "0:a",
            "-map", "0:v?",
            "-c:v", "copy",
            "-c:a", "libmp3lame",
            "-q:a", options.quality,
            "-id3v2_version", "3",
            "-map_metadata", "0",
            str(temporary_path),
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, env=ffmpeg_environment()
        )
        if result.returncode != 0:
            return ConversionResult(source, ConversionStatus.ERROR, f"ERREUR : {result.stderr.strip()}")

        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as exc:
        return ConversionResult(source, ConversionStatus.ERROR, f"ERREUR : {exc}")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    if options.delete_sources:
        try:
            source.unlink()
        except OSError as exc:
            return ConversionResult(
                source,
                ConversionStatus.ERROR,
                f"ERREUR : MP3 créé, mais suppression de l’original impossible : {exc}",
            )
        return ConversionResult(source, ConversionStatus.SUCCESS, "converti (original supprimé)")
    return ConversionResult(source, ConversionStatus.SUCCESS, "converti")
