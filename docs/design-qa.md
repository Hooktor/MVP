# Design QA — tableau de bord « À traiter maintenant »

Date : 23 septembre 2026
Viewport contrôlé : 1440 × 1024, session `demo.fournisseur`

## Référence contrôlée

Concept « Decision Focus » validé par l’utilisateur : tableau de bord opérationnel avec bandeau de recherche, titre prioritaire, filtres de catégories, file d’actions en six colonnes et panneaux de synthèse.

## Vérifications

- Hiérarchie : titre, sous-titre et CTA « Nouvelle demande » visibles dès l’arrivée.
- Navigation : six catégories d’actions sont présentes et mènent aux écrans existants.
- File opérationnelle : type, description, filiale, échéance, avancement et action sont lisibles sur une ligne.
- Fidélité métier : chaque ligne provient des demandes, sollicitations ou missions visibles pour l’utilisateur connecté ; aucune donnée décorative n’a été ajoutée.
- Accessibilité : en-têtes de tableau, libellés de navigation et actions explicites conservés ; l’adaptation mobile masque seulement les colonnes secondaires.
- Compatibilité : `manage.py check` sans erreur et suite Django complète validée (27 tests).

## Résultat final

**passed** — rendu vérifié dans Chrome, sans erreur visuelle ou fonctionnelle bloquante.
