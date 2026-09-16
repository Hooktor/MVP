from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from orbit_app.models import Profile
class Command(BaseCommand):
    help='Crée les groupes ORBIT de manière idempotente.'
    def handle(self,*args,**kwargs):
        for code,label in Profile.ROLE_CHOICES:
            group,_=Group.objects.get_or_create(name=code)
            group.permissions.set(Permission.objects.filter(content_type__app_label='orbit_app'))
        self.stdout.write(self.style.SUCCESS('Rôles ORBIT initialisés.'))
