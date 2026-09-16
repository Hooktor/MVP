# ORBIT

Application Django de gestion du sourcing d’experts, des sollicitations et des missions.

## Installation

Python 3.11+ et Django 4.2 sont requis. Dans un environnement virtuel : `pip install -r requirements.txt`, puis `python manage.py migrate`, `python manage.py seed_roles`, `python manage.py seed_demo_data` et `python manage.py runserver`.

SQLite est utilisé par défaut. PostgreSQL est activable avec `DATABASE_URL` (voir `.env.example`). L’email utilise la console en développement.

## Démonstration

Les comptes `demo.demandeur`, `demo.fournisseur` et `demo.omea` sont créés par le seed. Mot de passe de démonstration : `ORBIT-demo-2026` (à changer hors démonstration).

## Commandes

`python manage.py test` · `python manage.py process_timeouts` · `python manage.py send_pending_reminders`.

Les transitions critiques sont centralisées dans `orbit_app/services.py`, avec transactions, contrôle de rôle, audit et notifications.
