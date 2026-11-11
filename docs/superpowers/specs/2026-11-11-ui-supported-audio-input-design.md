# Formats audio pris en charge dans l’UI — conception

- **Intention :** permettre dans l’interface Qt la sélection individuelle et l’ajout récursif des mêmes formats audio que le cœur traite déjà : `.m4a`, `.wav`, `.aiff` et `.aif` (casse insensible).
- **Approche :** remplacer les appels UI limités à `is_m4a` / `discover_m4a` par `is_supported_audio` / `discover_audio`, et garder le filtre du sélecteur de fichiers aligné sur `SUPPORTED_AUDIO_EXTENSIONS`. Aucun changement au moteur de conversion ni au CLI.
- **Comportement conservé :** glisser-déposer, ajout de dossiers, arborescence d’entrée, pochettes, sorties et options existantes. Les noms générés en collision continuent de suivre les règles existantes.
- **Hors périmètre :** ajout de nouveaux codecs/formats, changement de dépendances ou de format de sortie. Les seuls formats annoncés sont ceux définis par le cœur.
