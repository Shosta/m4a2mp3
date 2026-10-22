import os
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


def is_m4a(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".m4a" and not path.name.startswith("._")


def discover_m4a(directory: Path, on_error: Optional[Callable[[Path, OSError], None]] = None) -> list[Path]:
    files = []
    try:
        candidates = directory.rglob("*")
        for candidate in candidates:
            try:
                if is_m4a(candidate):
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


def convert_file(source: Path, options: ConversionOptions) -> ConversionResult:
    destination = source.with_suffix(".mp3")
    if destination.exists() and not options.overwrite:
        return ConversionResult(source, ConversionStatus.SKIPPED, "ignoré (mp3 déjà présent)")

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=source.parent, suffix=".mp3", delete=False) as temporary_file:
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
