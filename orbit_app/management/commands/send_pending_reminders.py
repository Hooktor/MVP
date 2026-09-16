from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from orbit_app.models import ExpertSolicitation, Notification
class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        now=timezone.now(); count=0
        for s in ExpertSolicitation.objects.select_related('expert','request').filter(status='PENDING'):
            hours=(now-s.created_at).total_seconds()/3600 if hasattr(s,'created_at') else 0
            key='24' if hours>=24 else '0'
            if key not in s.reminders_sent:
                profile=s.expert.subsidiary.profiles.filter(role='ADMIN_FOURNISSEUR').first()
                if profile: Notification.objects.create(user=profile.user,title='Rappel de sollicitation',message=s.request.reference); s.reminders_sent[key]=now.isoformat(); s.save(update_fields=['reminders_sent']); count+=1
        self.stdout.write(f'{count} rappel(s) envoyé(s).')
