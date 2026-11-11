# Organisation MP3 par métadonnées — plan d’implémentation

> **Pour les agents d’implémentation :** sous-compétence requise : `superpowers:subagent-driven-development` (recommandée) ou `superpowers:executing-plans`. Avancer tâche par tâche et cocher les étapes.

**Objectif :** Ajouter une destination facultative `--sortie` / GUI qui produit `destination/Artiste/Album/nom-source.mp3` d’après les tags, avant de convertir chaque fichier.

**Architecture :** `core.py` fournit la lecture des tags avec `ffprobe`, le calcul sécurisé des destinations et l’écriture atomique vers le dossier cible. CLI et GUI préparent le lot, excluent les métadonnées illisibles et les collisions entre fichiers, puis affichent les chemins résultants ; l’omission de destination garde le chemin de sortie actuel sans `ffprobe`.

**Technologies :** Python standard library, `ffprobe` et `ffmpeg` externes, Qt existant.

**Spécification :** `docs/superpowers/specs/2026-11-11-metadata-output-layout-design.md`

## Contraintes globales

- Rester sur la branche actuelle `ui-improvement` et préserver les éléments existants dans `docs/`.
- Aucune dépendance Python ajoutée ; réutiliser `ffmpeg_environment()` pour les sous-processus FFmpeg/frozen.
- Dossiers exacts : `Artiste inconnu` et `Album inconnu` pour tags manquants ou vides.
- `morceau.m4a` devient `morceau.mp3`; les MP3 sont rangés dans `destination/Artiste/Album/`.
- Lire les métadonnées de tout le lot avant les conversions ; ignorer et signaler les erreurs `ffprobe` et les seules entrées impliquées par les collisions.
- Sans destination, le comportement actuel reste inchangé.
- Créer les dossiers manquants ; le fichier temporaire doit être dans le dossier cible pour que `os.replace` soit atomique.

## Fichiers concernés

- `core.py` : interfaces de lecture des tags, calcul du chemin destination et conversion sûre vers un chemin donné.
- `m4a2mp3.py` : option `--sortie`, préparation complète des destinations, erreurs/collisions et conversions.
- `gui_qt.py` : sélection de destination, préparation du lot avant conversions parallèles, transfert et rendu du chemin réel.
- `ui/source_tree.py` : collisions d’entrées selon le chemin cible calculé, pas selon le voisin du fichier source.
- `ui/result_tree.py` : affichage de la hiérarchie et du chemin MP3 réel en sortie.
- `test_core_audio_formats.py` et nouveaux tests ciblés au besoin : couverture unitaire et tests des appels sous-processus simulés.
- `README.md` : exemples et options GUI/CLI mis à jour.

## Points de revue

- Tags artiste/album vides, espaces seuls ou absents → chemins inconnus exacts ; test dans tâche 1.
- Tags contenant séparateurs, `..`, caractères invalides ou valeur absolue → chemin reste strictement sous le dossier de destination ; test dans tâche 1.
- Sortie `ffprobe` invalide ou erreur d’exécution → entrée en erreur sans conversion correspondante ; tests tâche 1 et intégration tâche 2.
- Plusieurs fichiers du lot visent le même chemin → seulement les entrées en conflit sont exclues avant lancement des conversions ; tests tâches 2 et 3.
- Échec FFmpeg ou dossier destination impossible à créer → pas de MP3 partiel, original préservé, erreur rapportée ; test tâche 1.

---

### Task 1 : Résolution des tags et conversion vers une destination atomique

**Fichiers :**
- Modifier : `core.py`
- Modifier : `test_core_audio_formats.py`

**Interfaces :**
- Produire `read_audio_tags(source: Path) -> tuple[str, str]`, avec artiste puis album ; lancer `ffprobe` en JSON pour le format/audio, normaliser les tags absents/vides vers les chaînes inconnues, lever `OSError`/`ValueError` pour tout échec de lecture ou contenu invalide.
- Produire `output_path_from_tags(source: Path, output_root: Path, artist: str, album: str) -> Path` qui assainit les noms de dossiers et retourne la cible sous `output_root` avec suffixe `.mp3`.
- Maintenir `convert_file(source, options, destination=None)` et créer les parents; placer le temporaire dans `destination.parent`.

- [ ] **Étape 1 : écrire les tests en échec** pour extraction `artist`/`album` (y compris casse courante des clés de tags), tags absents/vides, JSON/sous-processus invalide, assainissement et confinement des chemins, création de dossier/temp dans destination, échec FFmpeg préservant la source.
- [ ] **Étape 2 : vérifier l’échec** avec `python3 -m unittest test_core_audio_formats -v` ; attendu : les nouvelles interfaces/tests échouent.
- [ ] **Étape 3 : implémenter les interfaces** dans `core.py`, en utilisant `subprocess.run(..., capture_output=True, text=True, env=ffmpeg_environment())` et une temporisation raisonnable pour `ffprobe`; utiliser `Path.resolve()`/une vérification de confinement contre les chemins échappant à la racine.
- [ ] **Étape 4 : vérifier** avec `python3 -m unittest test_core_audio_formats -v` ; attendu : tous les tests passent, sans dépendre de FFmpeg réel.

### Task 2 : CLI et orchestration par lot

**Fichiers :**
- Modifier : `m4a2mp3.py`
- Créer/Modifier : `test_cli_output.py` (tests avec patch des sous-processus et conversions)

**Interfaces :**
- Consommer les interfaces `read_audio_tags`, `output_path_from_tags` et `convert_file` de la tâche 1.
- Ajouter `--sortie` de type `Path`, facultatif.

- [ ] **Étape 1 : écrire des tests en échec** pour la destination hiérarchique, l’absence de `ffprobe` sans `--sortie`, échec de tags exclu avant toute conversion, collision n’exécutant aucune conversion pour les seuls conflits, et maintien des arguments/chemins existants sans `--sortie`.
- [ ] **Étape 2 : vérifier l’échec** avec `python3 -m unittest test_cli_output -v`.
- [ ] **Étape 3 : implémenter** la prélecture des tags et la préparation de toutes les cibles avant de soumettre les tâches; détecter collisions insensibles à la casse via `os.path.normcase`; transmettre `destination=` à `convert_file`; afficher les erreurs de préparation dans le bilan.
- [ ] **Étape 4 : vérifier** `python3 -m unittest test_cli_output -v` et `python3 m4a2mp3.py --help`.

### Task 3 : GUI, destination commune et arbres de résultats

**Fichiers :**
- Modifier : `gui_qt.py`
- Modifier : `ui/source_tree.py`
- Modifier : `ui/result_tree.py`
- Créer/Modifier : tests GUI ciblés selon l’environnement Qt disponible

**Interfaces :**
- `ConversionTask` reçoit la destination effective calculée et passe celle-ci à `convert_file`.
- `ResultTree.add_result` reçoit la destination réelle et construit l’arbre d’après `destination.relative_to(output_root)` lorsque sortie activée ; sans destination, conserve l’affichage actuel.

- [ ] **Étape 1 : écrire les tests** pour champ/sélecteur de dossier commun, métadonnées et collisions préparées avant de lancer les tâches, résultat montrant le vrai chemin `Artiste/Album`, erreurs de `ffprobe` visibles et absence de conversion pour l’entrée en erreur.
- [ ] **Étape 2 : vérifier le comportement attendu** avec les tests GUI disponibles ; s’ils requièrent Qt absent, noter la dépendance et garder les tests des résolveurs/planificateurs isolés de Qt.
- [ ] **Étape 3 : implémenter** le bouton et le champ de destination avec `QFileDialog.getExistingDirectory`, préparer le lot de manière synchrone avant l’envoi au `QThreadPool`, ajuster le bookkeeping de collision de `SourceTree` aux sorties planifiées, et afficher la destination réelle dans `ResultTree`.
- [ ] **Étape 4 : vérifier** tous les tests GUI possibles et lancer `python3 gui_qt.py` uniquement si PyQt et FFmpeg sont disponibles.

### Task 4 : Documentation et vérification finale

**Fichiers :**
- Modifier : `README.md`

- [ ] **Étape 1 : ajouter** aux exemples CLI `--sortie` et documenter la structure artiste/album, valeurs de tags manquantes, traitement des métadonnées illisibles et choix de destination du GUI.
- [ ] **Étape 2 : vérifier** `python3 -m unittest discover -v`, `python3 -m py_compile core.py m4a2mp3.py gui_qt.py ui/source_tree.py ui/result_tree.py`, `python3 m4a2mp3.py --help`.
- [ ] **Étape 3 : vérifier** le diff et le statut de la branche pour confirmer que les seuls changements sont les fichiers de fonctionnalité/tests/docs attendus, sans modification d’autres données préexistantes.
