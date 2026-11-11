# Destination par métadonnées — conception

## Intention et périmètre

Ajouter une destination facultative `--sortie` au CLI et un sélecteur équivalent au GUI. Quand elle est renseignée, l’application organise les MP3 sous `destination/Artiste/Album/nom-source.mp3`, en utilisant les tags audio et les valeurs `Artiste inconnu` / `Album inconnu` si ceux-ci sont absents. Le nom de base du fichier source est conservé. Sans destination, le comportement existant (MP3 à côté de la source) reste inchangé.

## Approche retenue

Lire les tags avant toute conversion avec `ffprobe` (fourni avec FFmpeg), déterminer l’ensemble des destinations et les collisions, puis convertir directement vers les chemins finaux. `convert_file` créera les répertoires parents et utilisera un fichier temporaire dans le dossier destination afin que `os.replace` reste atomique. Le GUI affichera les destinations réelles.

L’alternative de convertir puis déplacer les MP3 est écartée : elle ajoute des opérations de déplacement et complique la gestion des collisions ainsi que l’écriture atomique. Les métadonnées ne seront pas utilisées pour organiser les fichiers lorsque `--sortie` n’est pas renseigné afin de préserver le comportement actuel.

## Contraintes et décisions

- Rester sur la branche git actuelle `ui-improvement` et préserver les fichiers déjà présents dans `docs/`.
- Pas de nouvelle dépendance Python ; `ffprobe` est exécuté en sous-processus avec l’environnement FFmpeg du projet.
- Tags artiste/album absents ou vides : `Artiste inconnu` / `Album inconnu`.
- Le nom du fichier source est conservé comme nom de base avec sa seule extension remplacée par `.mp3` (par exemple `morceau.m4a` devient `morceau.mp3`).
- Les chemins issus des tags doivent être assainis pour rester sous la destination et être valides comme noms de répertoires.
- Le GUI expose une destination commune choisie par l’utilisateur ; le CLI la reçoit avec `--sortie`. Sous cette destination, le chemin est `Artiste/Album/nom-source.mp3`.
- Les tags absents ou vides donnent `Artiste inconnu` et `Album inconnu`.
- Les métadonnées de tous les fichiers sont lues avec `ffprobe` avant de lancer les conversions. Si `ffprobe` échoue pour un fichier, ce fichier est signalé et ignoré ; les autres continuent.
- Les collisions entre fichiers du lot sont détectées avant conversion ; seuls les fichiers impliqués sont signalés et ignorés. Le comportement d’écrasement existant s’applique aux fichiers déjà présents à destination.
- Les répertoires parents sont créés automatiquement et le fichier temporaire est créé dans le répertoire cible afin de conserver l’atomicité de `os.replace`.
- Sans destination, aucune lecture de métadonnées n’est nécessaire et le comportement actuel reste inchangé.

## Hors périmètre

Pas de changement des tags audio, pas de réorganisation des sources, pas de modification du comportement de conversion lorsque la destination est omise.
