# Design QA — Recherche d’experts (direction 3)

## Cible et capture

- Source visuelle choisie : `C:\Users\hamza\.codex\generated_images\01a09d1a-b9cc-75f3-90ef-70978fd4bcc1\exec-5c3b4bb6-5407-440b-892f-52c13540f77e.png` — 1487 × 1058 px.
- Implémentation : `http://127.0.0.1:8000/matching/`, capture affichée dans l’onglet Codex In-app Browser actif — 1280 × 720 px (capture visible pendant cette QA, non exportable par l’API CUA vers un fichier local).
- Densité : facteur de densité non exposé par l’aperçu intégré ; aucune normalisation pixel ni comparaison côte à côte archivée.
- État principal : recherche libre, 62 profils disponibles, shortlist vide. États interactionnels vérifiés séparément : deux profils sélectionnés, comparaison ouverte, retour à la liste vide, filtre par demande.

## Limite de vérification

Le rendu réel et la maquette source ont été inspectés, mais leurs captures n’ont pas pu être réunies dans un même artefact de comparaison au même viewport : la capture CUA est affichable dans l’aperçu mais n’est pas exportée sur disque et le viewport intégré est fixe. Conformément au protocole Product Design, la QA visuelle finale reste bloquée jusqu’à l’autorisation d’utiliser Playwright pour produire et comparer les captures normalisées. Les observations ci-dessous sont des vérifications visuelles et fonctionnelles, pas une revendication de fidélité pixel à pixel.

## Contrôle visuel — surfaces requises

- **Typographie :** Arial et les styles ORBIT existants sont conservés ; le titre, les libellés des filtres, les informations de ligne et les CTA gardent une hiérarchie cohérente. Le libellé long de navigation tient sur une ligne après ajustement local.
- **Espacement et rythme :** la page suit la composition choisie — zone de recherche, résultats en lignes, shortlist à droite. À 1280 × 720, les colonnes restent lisibles ; les règles responsive replient la shortlist sous les résultats sous 980 px et les lignes deviennent multi-lignes sous 760 px. Le rendu mobile n’a pas été capturé dans le navigateur.
- **Couleurs et tokens :** fond gris clair, cartes blanches, navigation charbon et accent Orange `#ff7900` utilisent les tokens de l’application ; états de disponibilité réutilisent les badges existants.
- **Images et icônes :** les icônes viennent de Tabler, déjà utilisé par ORBIT. La maquette comprend des portraits générés ; l’application conserve les avatars à initiales du système réel afin de ne pas attribuer de fausses photos à des personnes.
- **Copie :** le libellé de navigation est « Recherche d’experts ». La shortlist explique qu’elle sert à comparer, et que chaque sollicitation reste individuelle.

## Résultats et historique des corrections

- [P2 corrigé] L’état vide de la shortlist restait visible quand des éléments étaient sélectionnés, car le `display:flex` local prévalait sur l’attribut `hidden`. Ajout d’une règle explicite `[hidden]`; après correction, l’état vide disparaît à l’ajout et réapparaît après « Tout effacer ».
- Le panneau de comparaison s’active à partir de deux experts et affiche fonction, filiale, disponibilité, TJM, note, pertinence, domaines et compétences.
- La sélection et le retrait actualisent les cases et le compteur ; la sélection est conservée dans l’onglet pour la session.
- Le filtre par demande continue à rafraîchir les résultats via HTMX et affiche le score de correspondance calculé côté serveur.
- La sollicitation individuelle conserve le lien métier existant vers le formulaire direct de l’expert, sans demander d’associer une demande préexistante.

## Vérifications techniques

- `python manage.py check` : réussi.
- `python manage.py test orbit_app --verbosity 1` : 31 tests réussis.
- `node --check static/matching-workbench.js` : réussi.
- `git diff --check` : réussi (avertissements Git uniquement sur la conversion CRLF).
- Dans l’aperçu, ajout/retrait, conservation après rechargement, comparaison, filtre par demande et retour à l’état vide ont été vérifiés.

## Checklist d’implémentation

- [x] Renommer « Matching » en « Recherche d’experts » dans la sidebar.
- [x] Recomposer la page et rendre les résultats comparables.
- [x] Garder recherche, filtres, HTMX, pagination et parcours de sollicitation existants.
- [x] Construire une shortlist de session et une comparaison accessible.
- [ ] Capturer source et implémentation à viewport identique et les examiner dans une comparaison commune.
- [ ] Refaire un contrôle navigateur aux breakpoints mobile/tablette.

## À peaufiner

- [P3] Valider le rendu à 1440 × 1024, la cible exacte de la maquette, puis faire un passage mobile.
- [P3] Remplacer les avatars initiaux uniquement si ORBIT dispose de photos approuvées pour les experts.

final result: blocked

---

# Design QA — Sidebar ORBIT (concept choisi par l’utilisateur : 1)

## Références et état

- Source visuelle choisie : `C:\Users\hamza\.codex\generated_images\01a09d1a-b9cc-75f3-90ef-70978fd4bcc1\exec-68ce1103-9924-4607-9892-8e2a512f070b.png` — 1024 × 1536 px.
- Implémentation : `http://127.0.0.1:8000/matching/`, capture visible dans l’onglet Codex In-app Browser — 928 × 681 px.
- État contrôlé : sidebar ouverte au survol, section « Recherche d’experts » active. La sortie CUA ne fournit pas de chemin local ni de densité d’écran ; la capture ne peut donc pas être normalisée et placée côte à côte avec la source.

## Contrôle du rendu et limites

- Le panneau s’ouvre au-dessus du contenu et ne décale pas la zone de travail ; les libellés de navigation sont visibles et « Recherche d’experts » reste sur une ligne.
- La palette charbon/Orange, le logo textuel existant, les icônes Tabler et les données de compte réelles sont conservés.
- La fermeture par sortie du curseur et le déploiement au focus clavier sont déclarés en CSS ; l’aperçu CUA ne permet pas de déplacer librement le pointeur ni d’exporter une capture pour comparaison normalisée.
- Aucun problème fonctionnel manifeste n’a été observé dans l’état ouvert. La comparaison visuelle complète (typographie, mesures, couleurs et rythme) reste à effectuer avec deux captures côte à côte au même viewport.

## Checklist

- [x] Déploiement au survol / focus, repli lorsque le curseur quitte le rail, sans déplacement du contenu.
- [x] Navigation et liens conservés ; adaptation tactile existante préservée.
- [x] Contrôle Django et vérification diff sans erreur.
- [ ] Captures source/implémentation normalisées et comparaison côte à côte.

final result: blocked — comparaison côte à côte non disponible dans l’aperçu navigateur actuel.
