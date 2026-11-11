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
    normalized_path_key,
    output_path_from_tags,
    read_audio_tags,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Conversion récursive M4A -> MP3")
    parser.add_argument("--dossier", type=Path, help="Dossier racine à parcourir")
    parser.add_argument("--sortie", type=Path, help="Dossier de destination des MP3 organisés par artiste/album")
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
    conversions = []
    if args.sortie is None:
        conversions = [(path, None) for path in files]
    else:
        prepared = []
        for path in files:
            try:
                artist, album = read_audio_tags(path)
                destination = output_path_from_tags(path, args.sortie, artist, album)
                prepared.append((path, destination))
            except (OSError, ValueError) as exc:
                errors += 1
                print(f"[préparation] {path.name} -> ERREUR : {exc}")

        destination_groups = {}
        for path, destination in prepared:
            destination_groups.setdefault(normalized_path_key(destination), []).append((path, destination))

        for group in destination_groups.values():
            if len(group) > 1:
                errors += len(group)
                for path, destination in group:
                    print(f"[préparation] {path.name} -> collision de destination : {destination}")
            else:
                conversions.append(group[0])

    with ThreadPoolExecutor(max_workers=options.jobs) as pool:
        if args.sortie is None:
            futures = [pool.submit(convert_file, path, options) for path, _ in conversions]
        else:
            futures = [pool.submit(convert_file, path, options, destination=destination)
                       for path, destination in conversions]
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result.status is ConversionStatus.ERROR:
                errors += 1
            print(f"[{index}/{len(conversions)}] {result.source.name} -> {result.message}")

    successes = sum(
        future.result().status is not ConversionStatus.ERROR
        for future in futures
    )
    print(f"\nTerminé : {successes} réussi(s), {errors} erreur(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
