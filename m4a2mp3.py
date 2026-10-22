#!/usr/bin/env python3
"""Convertit récursivement des fichiers M4A en MP3 en conservant les métadonnées."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core import (
    DEFAULT_JOBS,
    DEFAULT_OVERWRITE,
    DEFAULT_QUALITY,
    ConversionOptions,
    ConversionStatus,
    convert_file,
    discover_m4a,
    ffmpeg_available,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Conversion récursive M4A -> MP3")
    parser.add_argument("--dossier", type=Path, help="Dossier racine à parcourir")
    parser.add_argument("-q", "--qualite", default=DEFAULT_QUALITY,
                        help="Qualité VBR LAME : 0 (max) à 9 (min). Défaut : 0 (~245 kbps)")
    parser.add_argument("-j", "--jobs", type=int, default=DEFAULT_JOBS,
                        help=f"Nombre de conversions en parallèle. Défaut : {DEFAULT_JOBS}")
    parser.add_argument("--supprimer", action="store_true",
                        help="Supprime le .m4a après conversion réussie")
    parser.add_argument("--ecraser", action="store_true", default=DEFAULT_OVERWRITE,
                        help="Écrase les .mp3 déjà existants (comportement par défaut)")
    parser.add_argument("--ne-pas-ecraser", action="store_false", default=DEFAULT_OVERWRITE, dest="ecraser",
                        help="Ignore les .mp3 déjà existants")
    args = parser.parse_args()

    if not ffmpeg_available():
        print("ffmpeg est introuvable. Installe-le d'abord (brew install ffmpeg).", file=sys.stderr)
        return 1

    if args.dossier is None or not args.dossier.is_dir():
        print(f"Dossier introuvable : {args.dossier}", file=sys.stderr)
        return 1
    if args.jobs < 1:
        print("Le nombre de conversions simultanées doit être supérieur à zéro.", file=sys.stderr)
        return 1

    try:
        files = discover_m4a(args.dossier)
    except OSError as exc:
        print(f"Impossible de parcourir {args.dossier} : {exc}", file=sys.stderr)
        return 1

    if not files:
        print("Aucun fichier .m4a trouvé.")
        return 0

    options = ConversionOptions(
        quality=args.qualite,
        jobs=args.jobs,
        delete_sources=args.supprimer,
        overwrite=args.ecraser,
    )
    print(f"{len(files)} fichier(s) à traiter...\n")
    errors = 0
    with ThreadPoolExecutor(max_workers=options.jobs) as pool:
        futures = [pool.submit(convert_file, path, options) for path in files]
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result.status is ConversionStatus.ERROR:
                errors += 1
            print(f"[{index}/{len(files)}] {result.source.name} -> {result.message}")

    print(f"\nTerminé : {len(files) - errors} réussi(s), {errors} erreur(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
