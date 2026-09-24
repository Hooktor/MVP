from datetime import timedelta
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from .models import *
from .selectors import role

def audit(actor, action, obj, description, old='', new='', metadata=None):
    return AuditEvent.objects.create(actor=actor, action=action, entity_type=obj.__class__.__name__, entity_id=str(obj.pk), description=description, old_status=old or '', new_status=new or '', metadata=metadata or {})
def notify(user, title, message, url=''):
    return Notification.objects.create(user=user, title=title, message=message, url=url)
@transaction.atomic
def submit_request(request, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.status!='DRAFT': raise ValueError('La demande doit être un brouillon.')
    old=request.status; request.submitted_at=timezone.now()
    if request.mode=='DIRECT':
        expert=Expert.objects.select_for_update().get(pk=request.target_expert_id) if request.target_expert_id else None
        if not expert or expert.validation_status!='APPROVED' or expert.availability!='AVAILABLE': raise ValueError('L’expert ciblé n’est plus disponible.')
        request.status='WAITING_PRE_AGREEMENT'; request.save(update_fields=['status','submitted_at'])
        solicitation=ExpertSolicitation.objects.create(request=request,expert=expert,created_by=actor,deadline=timezone.now()+timedelta(hours=48))
        expert.availability='PRE_AGREEMENT'; expert.save(update_fields=['availability'])
        audit(actor,'SUBMIT_DIRECT_REQUEST',request,'Demande directe soumise',old,request.status,{'expert':expert.full_name})
        audit(actor,'CREATE_SOLICITATION',solicitation,'Sollicitation directe créée',metadata={'request':request.reference})
        for profile in Profile.objects.filter(role='ADMIN_FILIALE',subsidiary=expert.subsidiary).select_related('user'):
            notify(profile.user,'Pré-accord à traiter',f'{request.reference} · {expert.full_name}',f'/sollicitations/{solicitation.pk}/')
    else:
        request.status='WAITING_MATCHING'; request.save(update_fields=['status','submitted_at'])
        audit(actor,'SUBMIT_REQUEST',request,'Demande diffusée aux filiales',old,request.status)
        for profile in Profile.objects.filter(role='ADMIN_FILIALE').exclude(subsidiary_id=request.subsidiary_id).select_related('user'):
            notify(profile.user,'Nouvelle demande diffusée',f'{request.reference} · {request.title}',f'/demandes/{request.pk}/')
    return request

@transaction.atomic
def create_broadcast_proposal(request, expert, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.mode!='BROADCAST' or request.status!='WAITING_MATCHING': raise ValueError('Cette demande n’est plus ouverte aux propositions.')
    if expert.subsidiary_id==request.subsidiary_id: raise ValueError('Une filiale ne peut pas répondre à sa propre diffusion.')
    if expert.validation_status!='APPROVED' or expert.availability!='AVAILABLE': raise ValueError('Cet expert n’est pas disponible.')
    proposal,created=BroadcastProposal.objects.get_or_create(request=request,expert=expert,defaults={'proposed_by':actor})
    if not created: raise ValueError('Cet expert a déjà été proposé pour cette demande.')
    audit(actor,'CREATE_BROADCAST_PROPOSAL',proposal,'Expert proposé pour une demande diffusée',metadata={'request':request.reference})
    notify(request.requester,'Nouvelle proposition reçue',f'{expert.full_name} · {expert.subsidiary.name}',f'/demandes/{request.pk}/')
    return proposal

@transaction.atomic
def register_purchase_order(request, uploaded_file, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.status!='WAITING_PO': raise ValueError('Le PO ne peut être ajouté qu’après l’acceptation du pré-accord.')
    if not uploaded_file or not uploaded_file.name.lower().endswith('.pdf'):
        raise ValueError('Le bon de commande doit être un fichier PDF.')
    if uploaded_file.size>10*1024*1024: raise ValueError('Le bon de commande ne doit pas dépasser 10 Mo.')
    solicitation=request.solicitations.select_related('expert__subsidiary').filter(status='ACCEPTED').first()
    if not solicitation: raise ValueError('Aucun pré-accord accepté n’est associé à cette demande.')
    document=TransactionDocument.objects.create(request=request,file=uploaded_file,original_name=uploaded_file.name,document_type='PO',uploaded_by=actor)
    start=request.desired_start or timezone.localdate()
    mission=Mission.objects.create(request=request,expert=solicitation.expert,supplier_subsidiary=solicitation.expert.subsidiary,start_date=start,planned_end_date=start+timedelta(days=max(request.duration_days-1,0)),po_document=document,status='IN_PROGRESS')
    solicitation.expert.availability='ON_MISSION'; solicitation.expert.save(update_fields=['availability'])
    old=request.status; request.status='IN_PROGRESS'; request.save(update_fields=['status'])
    audit(actor,'REGISTER_PO',document,'Bon de commande déposé',old,request.status,{'request':request.reference,'mission':mission.pk})
    for profile in Profile.objects.filter(role='ADMIN_FILIALE',subsidiary=solicitation.expert.subsidiary).select_related('user'):
        notify(profile.user,'Mission planifiée',f'{request.reference} · PO reçu',f'/missions/{mission.pk}/')
    return mission

@transaction.atomic
def register_delivery_report(mission, uploaded_file, actor):
    mission=Mission.objects.select_for_update().select_related('request','expert','supplier_subsidiary').get(pk=mission.pk)
    if mission.request.status!='IN_PROGRESS' or mission.pv_document_id:
        raise ValueError('Le PV ne peut pas être ajouté à cette mission.')
    if not uploaded_file or not uploaded_file.name.lower().endswith('.pdf'):
        raise ValueError('Le procès-verbal doit être un fichier PDF.')
    if uploaded_file.size>10*1024*1024: raise ValueError('Le procès-verbal ne doit pas dépasser 10 Mo.')
    document=TransactionDocument.objects.create(request=mission.request,file=uploaded_file,original_name=uploaded_file.name,document_type='PV',uploaded_by=actor)
    mission.pv_document=document; mission.save(update_fields=['pv_document'])
    old=mission.request.status; mission.request.status='WAITING_EVALUATION'; mission.request.save(update_fields=['status'])
    audit(actor,'REGISTER_PV',document,'Procès-verbal déposé',old,mission.request.status,{'mission':mission.pk})
    notify(mission.request.requester,'PV à valider',f'{mission.request.reference} · évaluation à compléter',f'/missions/{mission.pk}/')
    return mission
@transaction.atomic
def create_solicitation(request, expert, actor):
    request=ExpertRequest.objects.select_for_update().get(pk=request.pk)
    if request.status not in ('WAITING_MATCHING','WAITING_PRE_AGREEMENT'): raise ValueError('La demande ne peut pas être sollicitée.')
    if expert.validation_status!='APPROVED' or expert.availability!='AVAILABLE': raise ValueError('Expert non éligible au matching.')
    s=ExpertSolicitation.objects.create(request=request,expert=expert,created_by=actor,deadline=timezone.now()+timedelta(hours=48)); expert.availability='PRE_AGREEMENT'; expert.save(update_fields=['availability']); request.status='WAITING_PRE_AGREEMENT'; request.save(update_fields=['status']); audit(actor,'CREATE_SOLICITATION',s,'Sollicitation créée',metadata={'request':request.reference}); return s
@transaction.atomic
def create_direct_solicitation(expert, actor, data):
    expert=Expert.objects.select_for_update().get(pk=expert.pk)
    if expert.validation_status!='APPROVED' or expert.availability!='AVAILABLE': raise ValueError('Cet expert n’est plus disponible.')
    subject=(data.get('subject') or '').strip()
    if not subject: raise ValueError('L’objet de la sollicitation est obligatoire.')
    duration=data.get('duration_days') or 1
    try: duration=max(1,int(duration))
    except (TypeError,ValueError): raise ValueError('La durée doit être un nombre de jours valide.')
    s=ExpertSolicitation.objects.create(expert=expert,created_by=actor,deadline=timezone.now()+timedelta(hours=48),subject=subject,message=(data.get('message') or '').strip(),desired_start=data.get('desired_start') or None,duration_days=duration,max_daily_rate=data.get('max_daily_rate') or None)
    expert.availability='PRE_AGREEMENT'; expert.save(update_fields=['availability'])
    audit(actor,'CREATE_DIRECT_SOLICITATION',s,'Sollicitation directe créée',metadata={'expert':expert.full_name})
    for profile in Profile.objects.filter(role='ADMIN_FILIALE',subsidiary=expert.subsidiary).select_related('user'):
        notify(profile.user,'Sollicitation directe à traiter',f'{subject} · {expert.full_name}',f'/sollicitations/{s.pk}/')
    return s
@transaction.atomic
def accept_solicitation(solicitation, actor):
    s=ExpertSolicitation.objects.select_for_update().select_related('request','expert').get(pk=solicitation.pk)
    if s.status!='PENDING' or role(actor)!='ADMIN_FILIALE' or actor.profile.subsidiary_id!=s.expert.subsidiary_id: raise ValueError('Action non autorisée.')
    old=s.status; s.status='ACCEPTED'; s.responded_at=timezone.now(); s.save(update_fields=['status','responded_at'])
    if s.request_id:
        s.request.status='WAITING_PO'; s.request.save(update_fields=['status']); notify(s.request.requester,'Sollicitation acceptée',s.request.reference)
    else:
        direct_request=create_direct_mission_file(s,s.created_by)
        notify(s.created_by,'Sollicitation directe acceptée','La demande est prête : ajoutez maintenant le bon de commande.',f'/demandes/{direct_request.pk}/')
    audit(actor,'ACCEPT_SOLICITATION',s,'Sollicitation acceptée',old,s.status); return s
@transaction.atomic
def refuse_solicitation(solicitation, actor, reason):
    if not reason.strip(): raise ValueError('Le motif de refus est obligatoire.')
    s=ExpertSolicitation.objects.select_for_update().select_related('request','expert').get(pk=solicitation.pk)
    if s.status!='PENDING' or role(actor)!='ADMIN_FILIALE' or actor.profile.subsidiary_id!=s.expert.subsidiary_id: raise ValueError('Action non autorisée.')
    s.status='REFUSED'; s.response_reason=reason; s.responded_at=timezone.now(); s.save(update_fields=['status','response_reason','responded_at'])
    if s.request_id: s.request.status='WAITING_MATCHING'; s.request.save(update_fields=['status']); notify(s.request.requester,'Sollicitation refusée',reason)
    else: notify(s.created_by,'Sollicitation directe refusée',reason,f'/sollicitations/{s.pk}/')
    s.expert.availability='AVAILABLE'; s.expert.save(update_fields=['availability']); audit(actor,'REFUSE_SOLICITATION',s,'Sollicitation refusée',new=s.status); return s
@transaction.atomic
def process_timeouts(now=None):
    now=now or timezone.now(); count=0
    for s in ExpertSolicitation.objects.select_for_update().filter(status='PENDING',deadline__lte=now):
        s.status='ESCALATED'; s.save(update_fields=['status'])
        if s.request_id: s.request.status='WAITING_MATCHING'; s.request.save(update_fields=['status'])
        s.expert.availability='AVAILABLE'; s.expert.save(update_fields=['availability']); audit(None,'SOLICITATION_TIMEOUT',s,'Sollicitation arrivée à échéance',new=s.status); count+=1
    return count
@transaction.atomic
def create_direct_mission_file(solicitation, actor):
    s=ExpertSolicitation.objects.select_for_update().select_related('expert','created_by__profile').get(pk=solicitation.pk)
    if s.request_id: return s.request
    if s.status!='ACCEPTED' or s.created_by_id!=actor.id: raise ValueError('Cette sollicitation directe ne peut pas encore devenir une mission.')
    subsidiary=actor.profile.subsidiary
    req=ExpertRequest.objects.create(title=s.subject,description=s.message or 'Sollicitation directe acceptée.',requester=actor,subsidiary=subsidiary,mode='DIRECT',target_expert=s.expert,status='WAITING_PO',desired_start=s.desired_start,duration_days=s.duration_days,max_daily_rate=s.max_daily_rate)
    s.request=req; s.save(update_fields=['request'])
    audit(actor,'CREATE_DIRECT_MISSION_FILE',req,'Dossier de mission créé après acceptation de la sollicitation directe',new='WAITING_PO',metadata={'solicitation':s.pk,'expert':s.expert.full_name})
    return req
@transaction.atomic
def create_evaluation(mission, actor, rating, comment):
    if actor!=mission.request.requester: raise ValueError('Seul le demandeur peut évaluer.')
    if mission.status!='IN_PROGRESS' or not comment.strip(): raise ValueError('Mission ou commentaire invalide.')
    e=Evaluation.objects.create(mission=mission,evaluator=actor,rating=rating,comment=comment); mission.status='COMPLETED'; mission.actual_end_date=timezone.now().date(); mission.save(update_fields=['status','actual_end_date']); mission.expert.average_score=Evaluation.objects.filter(mission__expert=mission.expert).aggregate(avg=Avg('rating'))['avg'] or 0; mission.expert.availability='AVAILABLE'; mission.expert.save(update_fields=['average_score','availability']); mission.request.status='CLOSED'; mission.request.save(update_fields=['status']); audit(actor,'CREATE_EVALUATION',e,'Évaluation créée',new='CLOSED'); return e
