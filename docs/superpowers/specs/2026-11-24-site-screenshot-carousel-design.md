# Carrousel de captures sur le site vitrine

- **Intention :** remplacer l’illustration provisoire du hero par les trois captures existantes, pour présenter les états réels de l’application sans refondre le site.
- **Périmètre :** garder la mise en page et les styles actuels ; intégrer un carrousel JavaScript natif, avec lecture automatique toutes les 5 secondes et commandes manuelles. Pas de dépendance externe.
- **Comportement :** afficher une capture à la fois, avec navigation accessible précédent/suivant et indicateurs ; suspendre la rotation au survol/focus et respecter `prefers-reduced-motion`.
- **Approche retenue :** HTML/CSS/JS existants (`docs/index.html`, `docs/assets/site.css`, `docs/assets/site.js`), pas de bibliothèque ni de nouveaux assets. La rotation automatique est retenue avec commandes manuelles, à la demande de l’utilisateur.
- **Validation :** vérifier les chemins d’images, les contrôles clavier, les commandes manuelles et rotation automatique via navigateur/local ; conserver une structure utilisable sans JavaScript autant que raisonnable.
