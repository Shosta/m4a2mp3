# Modernisation de l’interface Qt — conception

## Intention

Rendre le flux de conversion plus lisible et moderne sans modifier le comportement métier : les utilisateurs ajoutent leurs fichiers, choisissent éventuellement une sortie, ajustent quelques options, puis lancent la conversion.

## Direction retenue

Variante A : une barre d’actions horizontale en tête de fenêtre, au-dessus des deux panneaux de fichiers. Elle regroupe « Ajouter des fichiers… », « Ajouter un dossier… » et le choix du dossier de sortie. Les panneaux Entrées et Résultats occupent ensuite la largeur disponible ; un bandeau d’options et de progression ferme l’écran, avec « Convertir » clairement mis en avant.

## Options confirmées

- Trois qualités audio : Haute (`-q:a 0`), Équilibrée (`-q:a 4`) et Compacte (`-q:a 8`). Le réglage initial reste Haute, conforme au défaut actuel.
- Retirer le contrôle du nombre de conversions simultanées ; le traitement conserve 4 tâches parallèles en interne.
- Placer « Écraser les fichiers existants » et « Supprimer les fichiers source après conversion réussie » dans la zone d’options basse. Le libellé ne nomme pas M4A.
- Le champ de sortie reste facultatif et la destination choisie apparaît dans la barre d’actions.

## Portée et limites

- Cible : interface Qt existante dans `gui_qt.py` et `ui/options.py`, sans changement du CLI ni de la logique de conversion.
- Conserver les interactions d’ajout/dépôt, de sélection et suppression d’entrées, de choix de sortie, d’écrasement, de suppression source, de progression et de résultats.
- Préserver PyQt5/PyQt6, les chemins de sortie actuels et le thème natif du système ; employer une hiérarchie d’espacements, alignements et états Qt cohérents plutôt qu’une peau web étrangère aux contrôles natifs.
- Le résultat doit rester utilisable lorsque la fenêtre est redimensionnée ; entrées et résultats gardent une largeur équilibrée.
- Anti-objectifs : nouveaux réglages de parallélisme visibles, nouveau choix de thème, perte d’état existant, ou renommage affichant encore « M4A » comme seule source prise en charge.
