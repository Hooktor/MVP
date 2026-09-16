from django.core.management.base import BaseCommand
from orbit_app.services import process_timeouts
class Command(BaseCommand):
    def handle(self,*args,**kwargs): self.stdout.write(f'{process_timeouts()} sollicitation(s) traitée(s).')
