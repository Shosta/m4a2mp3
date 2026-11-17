# m4a-2-mp3

[![Build AppImage](https://github.com/Shosta/m4a2mp3/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/Shosta/m4a2mp3/actions/workflows/build-appimage.yml)
[![Deploy GitHub Pages](https://github.com/Shosta/m4a2mp3/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/Shosta/m4a2mp3/actions/workflows/deploy-pages.yml)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](#licence)

**Vos morceaux, prêts à emporter.** m4a-2-mp3 convertit vos fichiers audio M4A, WAV et AIFF en MP3, en conservant les métadonnées (titre, artiste, album) et les pochettes. Tout se passe en local, sur votre machine, avec une interface graphique Qt ou en ligne de commande.

- 🌐 **Site de présentation :** <https://shosta.github.io/m4a2mp3/>
- 📦 **Télécharger l'application (Linux) :** [page des Releases](https://github.com/Shosta/m4a2mp3/releases)

## Points forts

- **Conversion par lots :** ajoutez des fichiers ou des dossiers entiers ; les sous-dossiers sont parcourus récursivement.
- **Métadonnées et pochettes conservées :** titre, artiste, album et pochette intégrée suivent le fichier (selon ce que contient la source).
- **Résultats en direct :** l'interface affiche l'avancement et le résultat de chaque fichier au fur et à mesure.
- **Rangement automatique :** avec un dossier de sortie, les MP3 sont classés en sous-dossiers `artiste/album`.
- **Réglages :** qualité VBR, nombre de conversions en parallèle, écrasement des MP3 existants, suppression facultative des originaux.
- **100 % local :** aucun envoi de fichier vers un service externe.
- **Interface multilingue :** français, anglais et danois.
- **Formats d'entrée :** `.m4a`, `.wav`, `.aiff`, `.aif`.

## Site GitHub Pages

Le dépôt publie une page de présentation du projet, dans le dossier [`docs/`](docs/) :

| Élément | Rôle |
|---------|------|
| `docs/index.html` | Page statique de présentation (fonctions, mode d'emploi, prérequis) |
| `docs/assets/site.css` | Styles de la page |
| `docs/assets/site.js` | Sélecteur de langue FR / EN / DA |
| `docs/assets/interface-placeholder.svg` | Aperçu provisoire de l'interface (à remplacer par une vraie capture) |

La page propose un bouton de téléchargement vers les [Releases](https://github.com/Shosta/m4a2mp3/releases) et un lien vers le code source.

**Déploiement automatique :** le workflow [`deploy-pages.yml`](.github/workflows/deploy-pages.yml) publie le contenu de `docs/` à chaque push sur `main` (ou manuellement via *Run workflow*). Sur un fork, activez d'abord *Settings → Pages → Source : GitHub Actions*.

**Tester le site en local :**

```bash
python3 -m http.server --directory docs 8000
# puis ouvrir http://localhost:8000
```

## Installation

### Option 1 : AppImage (Linux x86_64)

Téléchargez `M4A2MP3-x86_64.AppImage` depuis la [page des Releases](https://github.com/Shosta/m4a2mp3/releases). Elle est construite automatiquement par le workflow [`build-appimage.yml`](.github/workflows/build-appimage.yml) et publiée à chaque tag `v*`.

```bash
chmod +x M4A2MP3-x86_64.AppImage
./M4A2MP3-x86_64.AppImage
```

FFmpeg doit être installé sur le système et disponible dans le `PATH`. Il n'existe pas de binaire Windows ou macOS pour l'instant : utilisez les sources.

### Option 2 : depuis les sources

Prérequis :

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/)
- PyQt6 ou PyQt5 (pour l'interface graphique uniquement)

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Debian / Ubuntu
winget install ffmpeg        # Windows
```

## Utilisation

### Interface graphique Qt

```bash
python3 gui_qt.py
```

Ajoutez ou déposez des fichiers `.m4a`, `.wav`, `.aiff` ou `.aif`, ou des dossiers contenant ces formats ; les dossiers sont parcourus récursivement. La liste de droite affiche les résultats au fur et à mesure. Les MP3 existants sont écrasés par défaut ; les options de qualité, de parallélisme, d'écrasement et de suppression des sources sont disponibles dans la fenêtre. Le bouton « Choisir la sortie… » permet de sélectionner un dossier de destination commun : les fichiers convertis y sont rangés dans des sous-dossiers artiste/album. Sans destination sélectionnée, chaque MP3 est créé à côté de son fichier source.

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

Avec `--sortie`, l'artiste et l'album sont lus dans les métadonnées du fichier ; les tags absents ou vides deviennent respectivement « Artiste inconnu » et « Album inconnu ». Si les métadonnées d'un fichier sont illisibles, celui-ci n'est pas converti, une erreur est signalée et les autres fichiers continuent d'être traités.

## Commande ffmpeg pour un seul fichier

```bash
ffmpeg -i "morceau.m4a" -map 0:a -map 0:v? -c:v copy -c:a libmp3lame -q:a 0 -id3v2_version 3 -map_metadata 0 "morceau.mp3"
```

## Remarques

- M4A (AAC) et MP3 sont des formats avec perte : la conversion re-compresse l'audio. Avec `-q 0`, la dégradation est quasi inaudible.
- Les fichiers protégés par DRM (`.m4p`) ne sont pas pris en charge.

## Licence

Logiciel libre sous licence MIT.
