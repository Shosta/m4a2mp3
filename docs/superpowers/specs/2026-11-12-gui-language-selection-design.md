# Sélection de la langue de l’application — conception

## Intention

Permettre à chacun d’utiliser l’interface graphique dans sa langue et de changer ce choix depuis les préférences. La structure doit faciliter l’ajout de langues ultérieurement.

## Approches

- **Catalogues Python par langue (retenu)** : aucune dépendance externe, ajout d’une langue par catalogue; cohérent avec cette application Python compacte.
- **Qt Linguist (`.ts`/`.qm`)** : solution native Qt, mais demande les outils de traduction et la gestion/installation de ressources supplémentaires.

## Direction retenue

Ajouter en première ligne des préférences une liste déroulante avec drapeaux et noms natifs pour Français, English et Dansk. Persister le code de langue dans `QSettings`; une langue invalide ou absente retombe sur le français. Appliquer le changement dès validation, y compris aux libellés de la fenêtre principale, aux préférences et aux dialogues utilisés par l’application. Organiser les chaînes dans des catalogues extensibles et ne pas introduire de dépendance de traduction.

## Portée et limites

- Traduire les chaînes de l’interface GUI, y compris titres, contrôles, infobulles, dialogues et messages d’état/erreur.
- Conserver les options de conversion et leur comportement; aucun changement au CLI ni au moteur de conversion.
- Afficher des drapeaux de pays avec les noms de langue natifs dans le sélecteur.
- Maintenir le support PyQt5/PyQt6 et l’empaquetage AppImage.
- Ajouter des langues ultérieurement sans modifier la logique de sélection ou de persistance.
