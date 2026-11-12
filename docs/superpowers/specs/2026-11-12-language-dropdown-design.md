# Sélecteur de langue — conception

## Intention

Remplacer les trois boutons `FR / EN / DA` par un sélecteur déroulant compact et explicite, afin que chaque langue soit reconnaissable par son drapeau et son nom.

## Portée

- Afficher le drapeau et le nom de la langue choisie dans le contrôle fermé.
- Proposer 🇫🇷 Français, 🇬🇧 English et 🇩🇰 Dansk dans la liste.
- Garder un `<select>` natif pour l’accessibilité clavier/lecteur d’écran et éviter une dépendance ou un menu personnalisé.
- Conserver la traduction courante de la page, la mise à jour de `lang`/métadonnées et la préférence `localStorage`.

## Approches

- Boutons enrichis avec drapeaux et noms : toujours visibles, mais occupent plus de place et n’offrent pas le menu demandé.
- Menu déroulant entièrement personnalisé : apparence contrôlée, mais complexité et responsabilités d’accessibilité non nécessaires.
- `<select>` natif avec options emoji-drapeau et nom : retenu par l’utilisateur, compact, accessible et sans dépendance ; son rendu ouvert varie selon le système.

## Vérification

Mettre à jour les tests du site pour vérifier les options, drapeaux, noms, changement de langue, état sélectionné et persistance après rechargement. Vérifier le rendu à desktop/mobile et exécuter toute la suite Python.
