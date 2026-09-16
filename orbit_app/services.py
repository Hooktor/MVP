from datetime import timedelta
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from .models import *

def audit(actor, action, obj, description, old='', new='', metadata=None):
    return AuditEvent.objects.create(actor=actor, action=action, entity_type=obj.__class__.__name__, entity_id=str(obj.pk), description=description, old_status=old or '', new_status=new or '', metadata=metadata or {})
def notify(user, title, message, url=''):
    return Notification.objects.create(user=user, title=title, message=message, url=url)
@transaction.atomic
def submit_request(request, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.status!='DRAFT': raise ValueError('La demande doit être un brouillon.')
    old=request.status; request.status='WAITING_MATCHING'; request.submitted_at=timezone.now(); request.save(update_fields=['status','submitted_at']); audit(actor,'SUBMIT_REQUEST',request,'Demande soumise',old,request.status); return request
@transaction.atomic
def create_solicitation(request, expert, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.status not in ('WAITING_MATCHING','WAITING_PRE_AGREEMENT'): raise ValueError('La demande ne peut pas être sollicitée.')
    if expert.validation_status!='APPROVED' or expert.availability!='AVAILABLE': raise ValueError('Expert non éligible au matching.')
    s=ExpertSolicitation.objects.create(request=request,expert=expert,created_by=actor,deadline=timezone.now()+timedelta(hours=48)); expert.availability='PRE_AGREEMENT'; expert.save(update_fields=['availability']); request.status='WAITING_PRE_AGREEMENT'; request.save(update_fields=['status']); audit(actor,'CREATE_SOLICITATION',s,'Sollicitation créée',metadata={'request':request.reference}); return s
@transaction.atomic
def accept_solicitation(solicitation, actor):
    s=ExpertSolicitation.objects.select_for_update().select_related('request','expert').get(pk=solicitation.pk)
    if s.status!='PENDING' or getattr(actor,'profile',None).role!='ADMIN_FOURNISSEUR' or actor.profile.subsidiary_id!=s.expert.subsidiary_id: raise ValueError('Action non autorisée.')
    old=s.status; s.status='ACCEPTED'; s.responded_at=timezone.now(); s.save(update_fields=['status','responded_at']); s.request.status='WAITING_PO'; s.request.save(update_fields=['status']); audit(actor,'ACCEPT_SOLICITATION',s,'Sollicitation acceptée',old,s.status); notify(s.request.requester,'Sollicitation acceptée',s.request.reference); return s
@transaction.atomic
def refuse_solicitation(solicitation, actor, reason):
    if not reason.strip(): raise ValueError('Le motif de refus est obligatoire.')
    s=ExpertSolicitation.objects.select_for_update().select_related('request','expert').get(pk=solicitation.pk)
    if s.status!='PENDING' or getattr(actor,'profile',None).role!='ADMIN_FOURNISSEUR' or actor.profile.subsidiary_id!=s.expert.subsidiary_id: raise ValueError('Action non autorisée.')
    s.status='REFUSED'; s.response_reason=reason; s.responded_at=timezone.now(); s.save(update_fields=['status','response_reason','responded_at']); s.request.status='WAITING_MATCHING'; s.request.save(update_fields=['status']); s.expert.availability='AVAILABLE'; s.expert.save(update_fields=['availability']); audit(actor,'REFUSE_SOLICITATION',s,'Sollicitation refusée',new=s.status); notify(s.request.requester,'Sollicitation refusée',reason); return s
@transaction.atomic
def process_timeouts(now=None):
    now=now or timezone.now(); count=0
    for s in ExpertSolicitation.objects.select_for_update().filter(status='PENDING',deadline__lte=now):
        s.status='ESCALATED'; s.save(update_fields=['status']); s.request.status='WAITING_MATCHING'; s.request.save(update_fields=['status']); s.expert.availability='AVAILABLE'; s.expert.save(update_fields=['availability']); audit(None,'SOLICITATION_TIMEOUT',s,'Sollicitation arrivée à échéance',new=s.status); count+=1
    return count
@transaction.atomic
def create_evaluation(mission, actor, rating, comment):
    if actor!=mission.request.requester: raise ValueError('Seul le demandeur peut évaluer.')
    if mission.status!='IN_PROGRESS' or not comment.strip(): raise ValueError('Mission ou commentaire invalide.')
    e=Evaluation.objects.create(mission=mission,evaluator=actor,rating=rating,comment=comment); mission.status='COMPLETED'; mission.actual_end_date=timezone.now().date(); mission.save(update_fields=['status','actual_end_date']); mission.expert.average_score=Evaluation.objects.filter(mission__expert=mission.expert).aggregate(avg=Avg('rating'))['avg'] or 0; mission.expert.availability='AVAILABLE'; mission.expert.save(update_fields=['average_score','availability']); mission.request.status='CLOSED'; mission.request.save(update_fields=['status']); audit(actor,'CREATE_EVALUATION',e,'Évaluation créée',new='CLOSED'); return e
