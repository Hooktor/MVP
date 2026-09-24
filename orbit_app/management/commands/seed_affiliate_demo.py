from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from orbit_app.models import Cluster, ExpertiseDomain, Expert, Profile, Skill, Subsidiary


AFFILIATES = [
    ("DMO1", "Orange Demo Atlas"), ("DMO2", "Orange Demo Baobab"),
    ("DMO3", "Orange Demo Cèdre"), ("DMO4", "Orange Demo Dune"),
    ("DMO5", "Orange Demo Ébène"), ("DMO6", "Orange Demo Falaise"),
]
FIRST_NAMES = ["Nora", "Ilyes", "Maya", "Samir", "Lina", "Yanis", "Inès", "Rayan", "Aya", "Malik"]
LAST_NAMES = ["Amani", "Kora", "Tarek", "Zina", "Siro", "Malo", "Nima", "Keli", "Dari", "Olan"]
ROLES = ["Architecte cloud", "Ingénieur réseau", "Data engineer", "Expert cybersécurité", "Chef de projet ICT"]


class Command(BaseCommand):
    help = "Crée 6 filiales fictives, leurs administrateurs et 60 experts de démonstration."

    def handle(self, *args, **options):
        cluster, _ = Cluster.objects.get_or_create(name="ORBIT · Données de démonstration")
        domain, _ = ExpertiseDomain.objects.get_or_create(name="ICT · Démonstration")
        skills = [Skill.objects.get_or_create(name=name, domain=domain)[0] for name in ("Cloud", "Réseau", "Data", "Cybersécurité", "Gestion de projet")]
        created_experts = 0

        for affiliate_index, (code, name) in enumerate(AFFILIATES, start=1):
            subsidiary, _ = Subsidiary.objects.get_or_create(code=code, defaults={"name": name, "cluster": cluster})
            username = f"demo.filiale{affiliate_index:02d}"
            user, _ = User.objects.get_or_create(username=username, defaults={"email": f"{username}@orbit.local", "first_name": "Admin", "last_name": f"Demo {affiliate_index}"})
            user.set_password("ORBIT-demo-2026")
            user.save(update_fields=["password"])
            Profile.objects.update_or_create(user=user, defaults={"role": "ADMIN_FILIALE", "subsidiary": subsidiary})

            for expert_index in range(1, 11):
                employee_id = f"{code}-FICT-{expert_index:02d}"
                expert, created = Expert.objects.get_or_create(
                    employee_id=employee_id,
                    defaults={
                        "first_name": FIRST_NAMES[(affiliate_index + expert_index - 2) % len(FIRST_NAMES)],
                        "last_name": LAST_NAMES[(affiliate_index * 3 + expert_index - 2) % len(LAST_NAMES)],
                        "job_title": ROLES[(affiliate_index + expert_index - 2) % len(ROLES)],
                        "subsidiary": subsidiary,
                        "validation_status": "APPROVED",
                        "availability": "AVAILABLE",
                        "daily_rate": 400 + ((affiliate_index * 37 + expert_index * 29) % 350),
                        "bio": "Profil fictif généré pour les démonstrations ORBIT.",
                    },
                )
                if created:
                    expert.domains.add(domain)
                    expert.skills.add(skills[(affiliate_index + expert_index - 2) % len(skills)])
                    created_experts += 1

        self.stdout.write(self.style.SUCCESS(f"6 filiales fictives prêtes, 6 administrateurs configurés et {created_experts} experts créés."))
        self.stdout.write("Comptes : demo.filiale01 à demo.filiale06 · mot de passe : ORBIT-demo-2026")
