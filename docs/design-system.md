# ORBIT — Enterprise Control Center
Direction retenue : première image Product Design, `docs/design/enterprise-control-center.png`.
Trois directions produites : centre de pilotage corporate, espace SaaS lumineux, centre opérationnel par échéance. Le premier est retenu pour sa lecture transversale des quatre rôles.

## Fondations
Arial/Helvetica locales, titres 32/17/14 px, texte métier 12–14 px, labels secondaires 10–12 px. Grille 4/8/12/16/24/32. Sidebar 232 px, topbar 64 px, marges de contenu 32 px. Rayon 5 px pour les contrôles, 8 px pour les surfaces. Ombres très légères.
Orange #ff7900, texte anthracite #17202b, fond #f4f5f7, surface blanche. Boutons orange à texte noir pour le contraste. Statuts lisibles avec texte et couleur.
Le mot-symbole ORBIT est typographique ; aucun logo Orange officiel n’est revendiqué.

## Composants
Shell fixe et drawer mobile, breadcrumb, tableau, grille experts, KPI, filtres, tags, badges, stepper, timeline, dialogue de confirmation, notifications, empty states et skeleton HTMX.
Icônes Tabler 3.34.1 servies localement. HTMX officiel 2.0.10 local ; aucun CDN nécessaire à l’exécution. Documentation : https://htmx.org/docs/ ; https://github.com/tabler/tabler-icons .

## Interactions
Recherche différée, filtres, pagination par fragments ; navigation classique en fallback. Le formulaire de sollicitation se charge en dialogue avec HTMX. Notifications en POST avec CSRF. Confirmations de soumission et acceptation. Les formulaires disposent de labels, erreurs et états d’envoi. Tabulation, focus visible et touche Échap pour les dialogues.

## Adaptations au modèle existant
Les valeurs de la maquette sont illustratives et ne sont pas injectées dans le dashboard. Aucune évolution fictive n’est affichée. L’urgence, le dépôt PO/PV et la validation OMEA ne disposent pas encore de workflows complets dans le socle : aucun faux bouton ne prétend les réaliser. Administration fonctionnelle en consultation. Les détails et missions restent liés aux objets réels.

