from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orbit_app.models import *
class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        son,_=Cluster.objects.get_or_create(name='Sonatel'); oci,_=Cluster.objects.get_or_create(name='OCI')
        sub,_=Subsidiary.objects.get_or_create(code='SN',defaults={'name':'Sonatel Sénégal','cluster':son})
        sub2,_=Subsidiary.objects.get_or_create(code='CI',defaults={'name':'OCI Côte d’Ivoire','cluster':oci})
        domain,_=ExpertiseDomain.objects.get_or_create(name='Data & IA')
        skill,_=Skill.objects.get_or_create(name='Python',domain=domain)
        for username,role,subs in [('demo.demandeur','ADMIN_FILIALE',sub),('demo.fournisseur','ADMIN_FILIALE',sub),('demo.ci','ADMIN_FILIALE',sub2),('demo.omea','ADMIN_OMEA',sub)]:
            user,_=User.objects.get_or_create(username=username,defaults={'email':f'{username}@orbit.local','first_name':username.split('.')[1].title()}); user.set_password('ORBIT-demo-2026'); user.save(); Profile.objects.update_or_create(user=user,defaults={'role':role,'subsidiary':subs})
        Expert.objects.get_or_create(employee_id='EXP-0001',defaults={'first_name':'Amina','last_name':'Diallo','job_title':'Data Engineer','subsidiary':sub,'validation_status':'APPROVED','bio':'Expert de démonstration','daily_rate':500})
        self.stdout.write(self.style.SUCCESS('Données de démonstration créées. Mot de passe démo: ORBIT-demo-2026'))
