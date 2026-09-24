from .selectors import role
def orbit_context(request):
    if not request.user.is_authenticated: return {}
    r = role(request.user)
    nav = [
        ('dashboard','layout-dashboard','Tableau de bord'),
        ('request_list','file-description','Demandes'),
        ('matching','focus-2','Recherche d’experts'),
        ('expert_list','users','Experts'),
        ('solicitation_list','send','Sollicitations'),
        ('mission_list','briefcase','Missions'),
        ('reports','chart-bar','Reporting'),
        ('audit_list','history','Journal d’activité'),
    ]
    if r == 'ADMIN_OMEA': nav.append(('functional_admin','settings','Administration'))
    return {'navigation': nav, 'business_role': r,
            'can_request': r in ('ADMIN_FILIALE','ADMIN_OMEA'),
            'can_expert': r in ('ADMIN_FILIALE','ADMIN_OMEA'),
            'can_solicit': r in ('ADMIN_FILIALE','ADMIN_OMEA'),
            'unread_count': request.user.notifications.filter(is_read=False).count()}
