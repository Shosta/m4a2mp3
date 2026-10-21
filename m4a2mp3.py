#!/usr/bin/env python3
"""Convertit récursivement des fichiers M4A en MP3 en conservant les métadonnées."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def _ffmpeg_environment() -> dict[str, str]:
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        original_library_path = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if original_library_path is None:
            env.pop("LD_LIBRARY_PATH", None)
        else:
            env["LD_LIBRARY_PATH"] = original_library_path
    return env


def convertir(src: Path, qualite: str, supprimer: bool, ecraser: bool) -> tuple[Path, str]:
    """Convertit un fichier. Retourne (fichier, statut)."""
    dst = src.with_suffix(".mp3")

    if dst.exists() and not ecraser:
        return src, "ignoré (mp3 déjà présent)"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=src.parent, suffix=".mp3", delete=False
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)

        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(src),
            "-map", "0:a",            # le flux audio
            "-map", "0:v?",           # la pochette, si elle existe
            "-c:v", "copy",
            "-c:a", "libmp3lame",
            "-q:a", qualite,          # VBR : 0 (meilleur) à 9 (plus petit)
            "-id3v2_version", "3",
            "-map_metadata", "0",     # conserve les tags (titre, artiste, album...)
            str(tmp_path),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, env=_ffmpeg_environment()
        )
        if result.returncode != 0:
            return src, f"ERREUR : {result.stderr.strip()}"

        os.replace(tmp_path, dst)
        tmp_path = None
    except OSError as exc:
        return src, f"ERREUR : {exc}"
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    if supprimer:
        try:
            src.unlink()
        except OSError as exc:
            return src, f"ERREUR : MP3 créé, mais suppression de l’original impossible : {exc}"
        return src, "converti (original supprimé)"
    return src, "converti"


def main() -> int:
    parser = argparse.ArgumentParser(description="Conversion récursive M4A -> MP3")
    parser.add_argument("--dossier", type=Path, help="Dossier racine à parcourir")
    parser.add_argument("-q", "--qualite", default="0",
                        help="Qualité VBR LAME : 0 (max) à 9 (min). Défaut : 0 (~245 kbps)")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                        help="Nombre de conversions en parallèle. Défaut : 4")
    parser.add_argument("--supprimer", action="store_true",
                        help="Supprime le .m4a après conversion réussie")
    parser.add_argument("--ecraser", action="store_true",
                        help="Écrase les .mp3 déjà existants")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("ffmpeg est introuvable. Installe-le d'abord (brew install ffmpeg).", file=sys.stderr)
        return 1

    if not args.dossier.is_dir():
        print(f"Dossier introuvable : {args.dossier}", file=sys.stderr)
        return 1

    fichiers = [p for p in args.dossier.rglob("*")
                if p.is_file()
                and p.suffix.lower() == ".m4a"
                and not p.name.startswith("._")]  # ignore les fichiers parasites macOS

    if not fichiers:
        print("Aucun fichier .m4a trouvé.")
        return 0

    print(f"{len(fichiers)} fichier(s) à traiter...\n")
    erreurs = 0

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(convertir, f, args.qualite, args.supprimer, args.ecraser)
                   for f in fichiers]
        for i, future in enumerate(as_completed(futures), 1):
            fichier, statut = future.result()
            if statut.startswith("ERREUR"):
                erreurs += 1
            print(f"[{i}/{len(fichiers)}] {fichier.name} -> {statut}")

    print(f"\nTerminé : {len(fichiers) - erreurs} réussi(s), {erreurs} erreur(s).")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
