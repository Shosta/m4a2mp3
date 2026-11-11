# m4a-2-mp3

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

### Interface graphique Qt

L’interface peut utiliser PyQt6 ou PyQt5 s’ils sont déjà installés dans votre environnement Python. Lancez-la avec :

```bash
python3 gui_qt.py
```

Une AppImage Linux x86_64 précompilée est disponible dans `M4A2MP3-x86_64.AppImage`. Rendez-la exécutable puis lancez-la :

```bash
chmod +x M4A2MP3-x86_64.AppImage
./M4A2MP3-x86_64.AppImage
```

FFmpeg doit être installé sur le système et disponible dans le `PATH`. L’icône de l’application provient de `ui/assets/m4a-2-mp3-icon.png`.

Déposez des fichiers `.m4a` ou des dossiers dans la liste de gauche ; les dossiers sont parcourus récursivement. La liste de droite affiche les résultats au fur et à mesure. Les MP3 existants sont écrasés par défaut ; les options de qualité, de parallélisme, d’écrasement et de suppression des sources sont disponibles dans la fenêtre. Le bouton « Choisir la sortie… » permet de sélectionner un dossier de destination commun : les fichiers convertis y sont rangés dans des sous-dossiers artiste/album. Sans destination sélectionnée, chaque MP3 est créé à côté de son fichier source.

### Ligne de commande

```bash
# Conversion simple (garde les .m4a et écrase les MP3 existants)
python3 m4a2mp3.py --dossier ~/Music/iTunes

# Organise les MP3 dans un dossier de destination par artiste et album
python3 m4a2mp3.py --dossier ~/Music/iTunes --sortie ~/Music/MP3

# Qualité ~190 kbps, 8 conversions en parallèle, sans écraser les MP3 existants
python3 m4a2mp3.py --dossier ~/Music/iTunes -q 2 -j 8 --ne-pas-ecraser

# Supprime les originaux après conversion réussie
python3 m4a2mp3.py --dossier ~/Music/iTunes --supprimer
```

## Options

| Option | Description |
|--------|-------------|
| `-q`, `--qualite` | Qualité VBR LAME de 0 (max, ~245 kbps) à 9 (min). Défaut : 0 |
| `-j`, `--jobs` | Conversions en parallèle. Défaut : 4 |
| `--sortie` | Dossier de destination des MP3, organisés en sous-dossiers artiste/album selon les métadonnées |
| `--supprimer` | Supprime le `.m4a` après conversion réussie |
| `--ecraser` | Écrase les `.mp3` déjà existants (par défaut) |
| `--ne-pas-ecraser` | Ignore les `.mp3` déjà existants |

Avec `--sortie`, l’artiste et l’album sont lus dans les métadonnées du fichier ; les tags absents ou vides deviennent respectivement « Artiste inconnu » et « Album inconnu ». Si les métadonnées d’un fichier sont illisibles, celui-ci n’est pas converti, une erreur est signalée et les autres fichiers continuent d’être traités.

## Commande ffmpeg pour un seul fichier

```bash
ffmpeg -i "morceau.m4a" -map 0:a -map 0:v? -c:v copy -c:a libmp3lame -q:a 0 -id3v2_version 3 -map_metadata 0 "morceau.mp3"
```

## Remarques

- M4A (AAC) et MP3 sont des formats avec perte : la conversion re-compresse l'audio. Avec `-q 0`, la dégradation est quasi inaudible.
- Les fichiers protégés par DRM (`.m4p`) ne sont pas pris en charge.
