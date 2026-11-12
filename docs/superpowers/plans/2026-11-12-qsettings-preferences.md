# Préférences QSettings — plan d’implémentation

> **Pour les agents d’implémentation :** suivre les étapes dans l’ordre et vérifier les tests.

**Objectif :** restaurer les quatre préférences de conversion GUI d’une session à l’autre.

**Architecture :** ajouter une fenêtre de préférences accessible depuis un bouton engrenage près du sélecteur de dossier. Utiliser `QSettings` avec des valeurs par défaut identiques aux valeurs actuelles, charger à la création de la fenêtre principale et sauvegarder à la validation de la fenêtre de préférences.

**Technologies :** Python, PyQt5/PyQt6 et `QSettings` déjà fourni par Qt.

**Spécification :** `docs/superpowers/specs/2026-11-12-qsettings-preferences-design.md`

## Contraintes globales

- Préserver la compatibilité PyQt5 et PyQt6.
- Préférences : dossier de sortie vide par défaut, qualité Haute (`"0"`), écrasement activé selon les valeurs actuelles, suppression des sources désactivée par défaut.
- Le choix de suppression reste explicite et visible dans la fenêtre principale lorsqu’il est activé.
- Aucun changement au CLI ni au moteur de conversion.

## Revue

- Une configuration QSettings vide applique les valeurs par défaut actuelles.
- Une qualité enregistrée hors des valeurs disponibles retombe sur Haute.
- Une préférence de suppression restaurée activée reste visible comme cochée dans l’interface principale.
- L’annulation de la fenêtre de préférences ne modifie pas les réglages actifs.
- Les dialogues de sélection des sources et dossiers de dialogue n’entrent pas dans le périmètre de persistance.

---

### Task 1 : Préférences persistantes et fenêtre de réglages

**Fichiers :**
- Modifier : `ui/qt_compat.py`, `ui/options.py`, `gui_qt.py`
- Modifier : `test_gui_qt.py`

- [ ] Ajouter les tests Qt : restaurer les quatre paramètres depuis QSettings; appliquer les défauts sur stockage vide; persister les modifications lors de la validation et ne rien changer après annulation; vérifier bouton engrenage et visibilité de la case Supprimer restaurée.
- [ ] Vérifier RED avec `python3 -m unittest -v test_gui_qt`.
- [ ] Exporter `QSettings` et le widget de dialogue nécessaire depuis `ui/qt_compat.py` pour PyQt5 et PyQt6.
- [ ] Créer une fenêtre de préférences avec dossier de sortie, liste de qualité, cases Écraser et Supprimer, avec valeurs initiales provenant des réglages courants et acceptation/annulation standard.
- [ ] Ajouter le bouton engrenage après « Parcourir… »; à l’acceptation, mettre à jour l’état principal, et charger/sauvegarder les préférences via `QSettings`.
- [ ] Vérifier GREEN avec `python3 -m unittest discover -v`, `python3 -m py_compile gui_qt.py ui/options.py ui/qt_compat.py test_gui_qt.py` et `git diff --check`.
