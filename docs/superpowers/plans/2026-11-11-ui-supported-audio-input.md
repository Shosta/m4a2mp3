# Formats audio dans l’interface — plan

> **Pour les agents d’implémentation :** suivre les étapes dans l’ordre et vérifier les tests.

**Objectif :** permettre à l’UI de sélectionner et d’ajouter tous les formats audio déjà supportés par le cœur.

**Architecture :** réutiliser `SUPPORTED_AUDIO_EXTENSIONS`, `is_supported_audio` et `discover_audio` dans la UI. Le CLI et le cœur de conversion ne changent pas.

**Technologies :** Python et PyQt existants.

**Spécification :** `docs/superpowers/specs/2026-11-11-ui-supported-audio-input-design.md`

## Contraintes globales

- Formats acceptés, casse insensible : `.m4a`, `.wav`, `.aiff`, `.aif`.
- Les fichiers individuels et la découverte récursive GUI utilisent le même prédicat central.
- Aucun changement au CLI ni au moteur de conversion.

## Revue

- Chaque format et variantes majuscules acceptés via sélection individuelle et dossiers récursifs.
- Formats non pris en charge et fichiers auxiliaires `._` restent exclus.

---

### Task 1 : Sélection et découverte des entrées audio GUI

**Fichiers :**
- Modifier : `ui/source_tree.py`, `gui_qt.py`
- Modifier : `test_gui_qt.py`
- Modifier : `README.md`

- [ ] Ajouter des tests Qt en échec pour ajout individuel, ajout récursif des quatre formats, et exclusion d’un format non supporté ; valider aussi le filtre du dialogue contre les extensions centrales.
- [ ] Vérifier RED avec `python3 -m unittest -v test_gui_qt`.
- [ ] Remplacer les helpers M4A-only par les helpers audio génériques et générer le filtre de dialogue depuis `SUPPORTED_AUDIO_EXTENSIONS`.
- [ ] Documenter les formats dans le README.
- [ ] Vérifier GREEN avec `python3 -m unittest discover -v`, `python3 -m py_compile gui_qt.py ui/source_tree.py test_gui_qt.py`, `python3 gui_qt.py --help` n/a; inspecter `git diff --check`.
