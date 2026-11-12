# Préférences GUI — conception

## Intention

Retrouver au prochain lancement les quatre préférences choisies pour les conversions : dossier de sortie, qualité, écrasement et suppression des sources.

## Direction retenue

Ajouter un bouton engrenage à droite de « Parcourir… », ouvrant une fenêtre dédiée aux préférences. `QSettings` restaure les valeurs au démarrage et les sauvegarde à la validation. Le réglage de suppression reste visible dans la fenêtre principale lorsqu’il est actif.

## Portée et limites

- Conserver PyQt5/PyQt6 et les valeurs par défaut existantes pour une première utilisation.
- Aucun changement du CLI, du moteur de conversion, ni à la fenêtre/taille ou aux dossiers des dialogues.
- La suppression des sources, désactivée par défaut, est persistée comme demandé et reste explicitement visible dans l’interface.
