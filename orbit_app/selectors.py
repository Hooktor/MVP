"""Scoped read models shared by the enterprise interface."""
from django.db.models import Q
from .models import Expert, ExpertRequest, ExpertSolicitation, Mission, AuditEvent

def role(user):
    if user.is_superuser: return 'ADMIN_OMEA'
    return getattr(getattr(user, 'profile', None), 'role', '')

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
    if role(user) == 'DEMANDEUR': return qs.filter(requester=user)
    if role(user) == 'ADMIN_FOURNISSEUR':
        return qs.filter(solicitations__expert__subsidiary_id=subsidiary_id(user)).distinct() if subsidiary_id(user) else qs.none()
    return qs.filter(subsidiary_id=subsidiary_id(user)) if subsidiary_id(user) else qs.none()

def solicitations_for(user):
    qs = ExpertSolicitation.objects.select_related('request__subsidiary','expert__subsidiary','created_by')
    if role(user) == 'ADMIN_OMEA': return qs
    if role(user) == 'ADMIN_FOURNISSEUR':
        return qs.filter(expert__subsidiary_id=subsidiary_id(user)) if subsidiary_id(user) else qs.none()
    return qs.filter(request__in=requests_for(user))

def missions_for(user):
    qs = Mission.objects.select_related('request','expert','supplier_subsidiary')
    if role(user) == 'ADMIN_OMEA': return qs
    if role(user) == 'ADMIN_FOURNISSEUR':
        return qs.filter(supplier_subsidiary_id=subsidiary_id(user)) if subsidiary_id(user) else qs.none()
    return qs.filter(request__in=requests_for(user))

def audit_for(user):
    qs = AuditEvent.objects.select_related('actor').order_by('-created_at')
    return qs if role(user) == 'ADMIN_OMEA' else qs.filter(actor=user)

