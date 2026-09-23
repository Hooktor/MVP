# ORBIT

ORBIT est une application Django interne de pilotage de l'expertise Orange Middle East and Africa. Elle relie les demandes de compétences aux profils experts, organise les pré-accords fournisseurs et conserve l'historique métier.

## Fonctionnalités

- Tableau de bord par périmètre métier.
- Référentiel experts, filtres et matching selon disponibilité, validation, domaine, compétence, langue et budget.
- Création et soumission de demandes d'expertise.
- Sollicitations fournisseurs avec délai de réponse de 48 heures, relances et escalade à échéance.
- Suivi des missions et évaluation de fin de mission.
- Notifications et journal d'audit.
- Import sécurisé de plusieurs experts depuis un fichier Excel `.xlsx`.
- Reporting et administration fonctionnelle en consultation.

## Rôles

| Rôle | Responsabilités principales |
| --- | --- |
| Demandeur | Crée ses demandes, suit les sollicitations associées et évalue ses missions. |
| Administrateur demandeur | Gère les demandes de sa filiale et lance les sollicitations. |
| Administrateur fournisseur | Gère les experts de sa filiale et répond aux pré-accords. |
| Administrateur OMEA | Dispose d'une vue transverse, valide les profils et consulte l'administration. |

## Workflow d'une demande

Le parcours affiché contient huit étapes : Demande, Matching, Pré-accord, PO attendu, Mission, PV, Évaluation et Clôture.

Les transitions déjà automatisées par l'application couvrent la soumission, le matching, l'acceptation ou le refus du pré-accord, l'escalade après 48 heures et la clôture après évaluation. Les écrans dédiés au dépôt des documents PO et PV restent à implémenter.

## Prérequis

- Python 3.11 ou version ultérieure
- pip
- SQLite pour le démarrage local, ou PostgreSQL via `DATABASE_URL`

## Démarrage local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_roles
python manage.py seed_demo_data
python manage.py seed_design_demo
python manage.py runserver
```

Ouvrir ensuite <http://127.0.0.1:8000/>.

## Comptes de démonstration

Après `seed_demo_data`, les comptes suivants sont disponibles. Le mot de passe est `ORBIT-demo-2026` et doit être remplacé hors démonstration.

| Compte | Rôle |
| --- | --- |
| `demo.demandeur` | Administrateur demandeur |
| `demo.fournisseur` | Administrateur fournisseur |
| `demo.omea` | Administrateur OMEA |

## Importer des experts depuis Excel

1. Se connecter comme administrateur fournisseur ou OMEA.
2. Ouvrir **Experts**, puis **Importer depuis Excel**.
3. Télécharger le modèle, renseigner les lignes, puis importer le fichier `.xlsx`.

Le fichier accepte au plus 500 lignes et 2 Mo. Les champs obligatoires sont le matricule, le prénom, le nom et la fonction. Les listes (domaines, compétences, certifications et verticales) sont séparées par des virgules. Les langues utilisent le format `Langue:Niveau`, par exemple `Français:C1, Anglais:B2`.

Un administrateur fournisseur ne peut importer que dans sa filiale et les profils sont créés au statut brouillon. OMEA peut choisir le statut de validation. Les lignes non valides sont signalées sans annuler les autres lignes correctes.

## Administration des filiales

L'écran ORBIT **Administration** est pour l'instant une vue de consultation. La création d'un cluster ou d'une filiale se fait avec un compte super-administrateur dans l'administration Django : <http://127.0.0.1:8000/admin/>. Créer d'abord le cluster, puis la filiale avec son nom, son code unique et son cluster.

## Commandes utiles

```powershell
python manage.py check
python manage.py test
python manage.py process_timeouts
python manage.py send_pending_reminders
```

`process_timeouts` escalade les sollicitations dépassant leur délai. `send_pending_reminders` crée les rappels pour les pré-accords en attente. En production, planifier ces commandes avec le planificateur choisi par l'équipe d'exploitation.

## Configuration

Les variables principales sont documentées dans `.env.example`.

- `DJANGO_SECRET_KEY` : clé Django, obligatoire hors développement.
- `DJANGO_DEBUG` : désactiver en production.
- `DJANGO_ALLOWED_HOSTS` : liste des hôtes autorisés.
- `DATABASE_URL` : URL PostgreSQL optionnelle.
- `TIME_ZONE` : fuseau horaire, par défaut `Africa/Casablanca`.
- `EMAIL_BACKEND` et `DEFAULT_FROM_EMAIL` : envoi des e-mails.

## Vérification

La suite couvre les règles de périmètre, les rôles, les demandes, le matching, les pré-accords, le refus, le timeout 48 h, l'évaluation et l'import Excel.

```powershell
python manage.py test
```

## Structure du projet

```text
orbit/                 Configuration Django
orbit_app/             Modèles, vues, services, sélecteurs et tests
templates/             Écrans et composants Django
static/                Styles, scripts, icônes et modèle Excel
docs/                  Documentation produit et design system
```

Les transitions métier critiques sont centralisées dans `orbit_app/services.py` afin de conserver les transactions, les contrôles de rôle, les notifications et les événements d'audit.
