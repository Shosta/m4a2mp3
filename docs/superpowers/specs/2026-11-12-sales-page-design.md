# Page de présentation — conception

## Intention

Créer une page de présentation pour m4a-2-mp3, destinée aux personnes qui veulent convertir des collections de fichiers audio en MP3 via l’interface graphique. L’action prioritaire est de télécharger l’AppImage Linux ; le code source et les instructions restent accessibles.

## Objectifs et limites

- Présenter en français, anglais et danois, avec un sélecteur de langue sur une seule page.
- Expliquer les formats pris en charge (M4A, WAV, AIFF), la conversion par lots, les métadonnées conservées, les options de qualité et l’organisation facultative par artiste/album.
- Montrer une illustration explicitement provisoire, remplaçable par une capture fournie par l’utilisateur.
- Ne pas inventer de tarifs, témoignages, mesures, systèmes téléchargeables ou capacités non documentées.
- Garder le site indépendant de l’application : HTML/CSS/JavaScript statiques, sans dépendance d’exécution.

## Publication et test

La page est hébergée dans `docs/` du dépôt existant. Un workflow GitHub Actions publie ce dossier sur GitHub Pages après chaque push sur `main`, avec déclenchement manuel possible. Test local via `python3 -m http.server 8000` exécuté depuis `docs/`.

## Approches

- Dépôt distinct : séparation du cycle de publication mais duplication de maintenance ; écarté.
- Générateur de site/framework : utile pour un site plus vaste mais ajoute une compilation et des dépendances inutiles à cette page ; écarté.
- Site statique dans le dépôt actuel : retenu, conformément au choix de l’utilisateur, simple à maintenir et directement déployable par Actions.

## Direction de page

Une page de vente responsive dans l’univers éditorial d’une pochette d’album : champ bleu-noir encré, papier chaud, accents vermillon et composition typographique évoquant une édition musicale. Le premier écran associe un titre lisible, une proposition factuelle, un aperçu provisoire de l’application et un appel direct vers la Release AppImage Linux. Le rythme de page et les détails graphiques s’inspirent d’une pochette et de ses notes, sans transformer la page en poster décoratif. La page expose les fonctions vérifiées, les prérequis FFmpeg/Python pour les autres usages et les liens vers le code et la licence MIT. Le sélecteur change tout le contenu, met à jour `lang` et mémorise la préférence ; français par défaut.

## Contraintes et décisions ouvertes

Le nom du produit et le dépôt existant sont conservés. Ne pas promettre la disponibilité de binaires autres que l’AppImage Linux. L’aperçu de l’interface reste un placeholder explicitement signalé et remplaçable par la capture d’écran que fournira l’utilisateur. Site statique HTML/CSS/JavaScript dans `docs/`, publié par GitHub Actions sur GitHub Pages.
