from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from orbit_app.models import *

class Command(BaseCommand):
    help='Ajoute des scénarios UI fictifs, identifiés DEMO-UI, sans modifier les données existantes.'

    @transaction.atomic
    def handle(self, *args, **options):
        user=User.objects.get(username='demo.demandeur')
        sub=user.profile.subsidiary
        now=timezone.now()
        data=[('Moussa','Diop','Architecte Cloud','Cloud & infrastructure','Azure','AVAILABLE'),('Fatou','Ndiaye','Experte cybersécurité','Cybersécurité','ISO 27001','PRE_AGREEMENT'),('Youssef','Benali','Ingénieur réseau MPN','Réseaux & MPN','5G','ON_MISSION'),('Salma','Traoré','Data Scientist','Data & IA','Python','AVAILABLE'),('Ibrahim','Kouamé','Consultant ITSM','Services IT','ITIL','PRE_AGREEMENT')]
        experts=[]
        for i,(first,last,job,domain,skill,status) in enumerate(data):
            d,_=ExpertiseDomain.objects.get_or_create(name=domain)
            s,_=Skill.objects.get_or_create(name=skill,defaults={'domain':d})
            expert,created=Expert.objects.get_or_create(employee_id=f'DEMO-UI-{i+1}',defaults={'first_name':first,'last_name':last,'job_title':job,'subsidiary':sub,'bio':'Profil fictif de démonstration ORBIT. Accompagnement des équipes projet, conception des solutions et transfert de compétences.','daily_rate':450+i*50,'available_from':now.date(),'validation_status':'APPROVED','availability':status})
            if created:
                expert.domains.add(d); expert.skills.add(s)
                language,_=Language.objects.get_or_create(name='Français')
                ExpertLanguageAssignment.objects.get_or_create(expert=expert,language=language,defaults={'level':'C1'})
                ProjectReference.objects.create(expert=expert,title='Programme de transformation — démonstration',description='Cadrage, conception et accompagnement du déploiement. Référence fictive.',client='Projet interne fictif',year=2026)
            experts.append(expert)
        titles=['Migration Cloud Infrastructure','Audit de sécurité du SI','Déploiement d’un réseau privé 5G','Plateforme analytique client','Amélioration des processus ITSM']
        states=['WAITING_MATCHING','WAITING_PRE_AGREEMENT','IN_PROGRESS','DRAFT','WAITING_PRE_AGREEMENT']
        for i,title in enumerate(titles):
            ref=f'DEMO-UI-2026-{i+1:04d}'
            req,created=ExpertRequest.objects.get_or_create(reference=ref,defaults={'title':title,'description':'Scénario fictif de démonstration. Mobiliser une expertise pour cadrer le besoin, accompagner la mise en œuvre et transmettre les compétences aux équipes locales.','requester':user,'subsidiary':sub,'domain':experts[i].domains.first(),'status':states[i],'desired_start':now.date()+timedelta(days=7),'duration_days':30,'max_daily_rate':700})
            if not created: continue
            req.required_skills.set(experts[i].skills.all())
            audit=AuditEvent.objects.create(actor=user,action='REQUEST_CREATED',entity_type='ExpertRequest',entity_id=str(req.pk),description=f'Demande créée : {title}',metadata={'demo':True})
            if i in (1,4):
                solicitation=ExpertSolicitation.objects.create(request=req,expert=experts[i],created_by=user,deadline=now+timedelta(hours=5 if i==4 else 21),status='PENDING')
                ExpertSolicitation.objects.filter(pk=solicitation.pk).update(created_at=solicitation.deadline-timedelta(hours=48))
                AuditEvent.objects.create(actor=user,action='CREATE_SOLICITATION',entity_type='ExpertSolicitation',entity_id=str(solicitation.pk),description=f'Pré-accord demandé : {experts[i].full_name}',metadata={'demo':True})
            if i==2:
                Mission.objects.create(request=req,expert=experts[i],supplier_subsidiary=sub,start_date=now.date()-timedelta(days=5),planned_end_date=now.date()+timedelta(days=25),status='IN_PROGRESS')
            Notification.objects.create(user=user,title='Démonstration : '+title,message='Scénario fictif disponible pour explorer le parcours ORBIT.',url=f'/demandes/{req.pk}/')
        self.stdout.write(self.style.SUCCESS('Scénarios DEMO-UI prêts. Aucun objet préexistant modifié.'))
