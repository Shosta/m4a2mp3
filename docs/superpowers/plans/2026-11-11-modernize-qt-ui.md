# Modernisation UI Qt — plan d’implémentation

> **Pour les agents d’implémentation :** utiliser `superpowers:executing-plans` ou `superpowers:subagent-driven-development` ; suivre les étapes et les vérifier.

**Objectif :** Réorganiser la fenêtre Qt selon la variante A et simplifier les réglages visibles.

**Architecture :** Barre d’actions en haut avec ajout et sortie, deux panneaux équilibrés sous celle-ci, options et progression dans le bandeau inférieur. `ui/options.py` garde la qualité et le parallélisme métier interne fixe à 4 ; `gui_qt.py` orchestre la disposition sans altérer le flux de conversion.

**Technologies :** Python, PyQt5/PyQt6 déjà utilisés.

**Spécification :** `docs/superpowers/specs/2026-11-11-modernize-qt-ui-design.md`

## Contraintes

- Qualités visibles : Haute `0`, Équilibrée `4`, Compacte `8`; défaut Haute.
- Retirer le contrôle visible des tâches simultanées, garder 4 en interne.
- Libellé de suppression source non lié à M4A.
- Conserver drag/drop, sélecteurs, résultats, progression, options et support PyQt5/6.

## Fichiers

- `ui/options.py` : trois niveaux qualité ; aucun contrôle de parallélisme.
- `gui_qt.py` : barre d’actions supérieure, panneaux de même poids, options/progression et bouton de conversion dans le bandeau bas ; libellés source génériques.
- `test_gui_qt.py` : assertions de contrôle de qualité, jobs par défaut et libellés/layout fonctionnel.

## Étapes

- [ ] Ajouter/adapter les tests Qt : trois valeurs/labels, défaut `0`, jobs internes à 4, absence de widget jobs et libellé de suppression générique.
- [ ] Réorganiser les layouts et appliquer les changements d’options sans modifier le flux de conversion.
- [ ] Exécuter `python3 -m unittest discover -v`, `python3 -m py_compile gui_qt.py ui/options.py test_gui_qt.py` et lancer le GUI en mode Qt offscreen pour valider son démarrage.
