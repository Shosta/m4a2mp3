# m4a2mp3

Convertit récursivement des fichiers `.m4a` (par exemple ripés avec iTunes) en `.mp3`, en conservant les métadonnées (titre, artiste, album, pochette).

## Prérequis

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/)

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Debian / Ubuntu
winget install ffmpeg        # Windows
```

## Utilisation

```bash
# Conversion simple (garde les .m4a)
python3 m4a2mp3.py ~/Music/iTunes

# Qualité ~190 kbps, 8 conversions en parallèle
python3 m4a2mp3.py ~/Music/iTunes -q 2 -j 8

# Supprime les originaux après conversion réussie
python3 m4a2mp3.py ~/Music/iTunes --supprimer
```

## Options

| Option | Description |
|--------|-------------|
| `-q`, `--qualite` | Qualité VBR LAME de 0 (max, ~245 kbps) à 9 (min). Défaut : 0 |
| `-j`, `--jobs` | Conversions en parallèle. Défaut : 4 |
| `--supprimer` | Supprime le `.m4a` après conversion réussie |
| `--ecraser` | Écrase les `.mp3` déjà existants |

## Commande ffmpeg pour un seul fichier

```bash
ffmpeg -i "morceau.m4a" -map 0:a -map 0:v? -c:v copy -c:a libmp3lame -q:a 0 -id3v2_version 3 -map_metadata 0 "morceau.mp3"
```

## Remarques

- M4A (AAC) et MP3 sont des formats avec perte : la conversion re-compresse l'audio. Avec `-q 0`, la dégradation est quasi inaudible.
- Les fichiers protégés par DRM (`.m4p`) ne sont pas pris en charge.
