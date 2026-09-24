"""Scoped read models shared by the enterprise interface."""
from django.db.models import Q
from .models import Expert, ExpertRequest, ExpertSolicitation, Mission, AuditEvent

def role(user):
    if user.is_superuser: return 'ADMIN_OMEA'
    stored_role=getattr(getattr(user, 'profile', None), 'role', '')
    # Les anciens rôles sont lus comme administrateurs de filiale afin que les
    # comptes existants conservent immédiatement leurs accès bilatéraux.
    return 'ADMIN_FILIALE' if stored_role in ('DEMANDEUR','ADMIN_DEMANDEUR','ADMIN_FOURNISSEUR') else stored_role

def subsidiary_id(user):
    return getattr(getattr(user, 'profile', None), 'subsidiary_id', None)

def experts_for(user, matching=False):
    qs = Expert.objects.select_related('subsidiary__cluster').prefetch_related('domains','skills','certifications','languages','verticals')
    if matching:
        return qs.filter(is_active=True, validation_status='APPROVED', availability='AVAILABLE')
    if role(user) != 'ADMIN_OMEA':
        qs = qs.filter(subsidiary_id=subsidiary_id(user)) if subsidiary_id(user) else qs.none()
    return qs

def requests_for(user):
    qs = ExpertRequest.objects.select_related('subsidiary','domain','requester').prefetch_related('required_skills')
    if role(user) == 'ADMIN_OMEA': return qs
    if not subsidiary_id(user): return qs.none()
    return qs.filter(Q(subsidiary_id=subsidiary_id(user))|Q(mode='BROADCAST',status='WAITING_MATCHING')).distinct()

def solicitations_for(user):
    qs = ExpertSolicitation.objects.select_related('request__subsidiary','expert__subsidiary','created_by')
    if role(user) == 'ADMIN_OMEA': return qs
    if not subsidiary_id(user): return qs.none()
    # Une sollicitation directe n'a pas encore de demande liée avant sa réponse.
    # Son créateur doit donc pouvoir la suivre pendant cette étape.
    return qs.filter(Q(created_by=user)|Q(request__subsidiary_id=subsidiary_id(user))|Q(expert__subsidiary_id=subsidiary_id(user))).distinct()

def missions_for(user):
    qs = Mission.objects.select_related('request','expert','supplier_subsidiary')
    if role(user) == 'ADMIN_OMEA': return qs
    if not subsidiary_id(user): return qs.none()
    return qs.filter(Q(request__subsidiary_id=subsidiary_id(user))|Q(supplier_subsidiary_id=subsidiary_id(user))).distinct()

def audit_for(user):
    qs = AuditEvent.objects.select_related('actor').order_by('-created_at')
    return qs if role(user) == 'ADMIN_OMEA' else qs.filter(actor=user)
