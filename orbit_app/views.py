from decimal import Decimal, InvalidOperation
from datetime import timedelta, date
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Avg, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import *
from .forms import ExpertForm, ExpertRequestForm
from .selectors import *
from .services import submit_request, create_solicitation, accept_solicitation, refuse_solicitation, audit

def listing(request, qs, template, partial, **ctx):
    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    params=request.GET.copy(); params.pop('page',None)
    ctx.update(page=page, q=request.GET.get('q',''), query=params.urlencode(), partial=partial)
    template=partial if request.headers.get('HX-Request') == 'true' else template
    return render(request,template,ctx)

def guard(user, roles):
    if role(user) not in roles: raise PermissionDenied

def request_writable(user,obj):
    return role(user) == 'ADMIN_OMEA' or (role(user) in ('DEMANDEUR','ADMIN_DEMANDEUR') and obj.subsidiary_id==subsidiary_id(user) and (role(user)=='ADMIN_DEMANDEUR' or obj.requester_id==user.id))

def with_deadline(s):
    remaining=(s.deadline-timezone.now()).total_seconds()
    s.deadline_level='expired' if remaining<=0 else 'critical' if remaining<6*3600 else 'warning' if remaining<24*3600 else 'normal'
    s.remaining='Échéance dépassée' if remaining<=0 else f'{int(remaining//3600)} h {int(remaining%3600//60):02d} min'
    return s

@login_required
def dashboard(request):
    reqs=requests_for(request.user); experts=experts_for(request.user); sols=solicitations_for(request.user); missions=missions_for(request.user)
    counts=dict(reqs.values('status').annotate(total=Count('id')).values_list('status','total'))
    response=sols.filter(status__in=['ACCEPTED','REFUSED'])
    total=response.count(); within=response.filter(responded_at__lte=F('deadline')).count()
    metrics=[('Demandes actives',reqs.exclude(status__in=['CLOSED','CANCELLED','DRAFT']).count(),'En cours de sourcing','file-description','request_list'),
      ('Pré-accords attendus',sols.filter(status='PENDING').count(),'Réponse sous 48 heures','clock','solicitation_list'),
      ('SLA respecté',f'{round(within/total*100)} %' if total else '—','Sur les réponses reçues','shield-check','reports'),
      ('Experts disponibles',experts.filter(availability='AVAILABLE',validation_status='APPROVED',is_active=True).count(),'Validés par OMEA','users','matching'),
      ('Missions en cours',missions.filter(status='IN_PROGRESS').count(),'Mobilisations actives','briefcase','mission_list')]
    pipeline=[('Matching',counts.get('WAITING_MATCHING',0),'blue'),('Pré-accord',counts.get('WAITING_PRE_AGREEMENT',0),'orange'),('PO attendu',counts.get('WAITING_PO',0),'orange'),('Mission',counts.get('IN_PROGRESS',0),'blue'),('Clôturées',counts.get('CLOSED',0),'green')]
    return render(request,'dashboard.html',{'title':'Vue d’ensemble','section':'dashboard','metrics':metrics,'pipeline':pipeline,
      'recent_requests':reqs.order_by('-created_at')[:5],'pending': [with_deadline(s) for s in sols.filter(status='PENDING').order_by('deadline')[:4]],
      'events':audit_for(request.user)[:5], 'available':experts.filter(availability='AVAILABLE',validation_status='APPROVED')[:3]})

def expert_filters(request,qs):
    q=request.GET.get('q','').strip()
    if q: qs=qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(job_title__icontains=q)|Q(skills__name__icontains=q)|Q(bio__icontains=q)|Q(references__description__icontains=q))
    for param,field in [('subsidiary','subsidiary_id'),('cluster','subsidiary__cluster_id'),('domain','domains__id'),('skill','skills__id'),('certification','certifications__id'),('language','languages__id')]:
        value=request.GET.get(param,'')
        if value.isdigit(): qs=qs.filter(**{field:value})
    if request.GET.get('availability') in dict(Expert.AVAILABILITY): qs=qs.filter(availability=request.GET['availability'])
    for param,field in [('rate','daily_rate__lte'),('score','average_score__gte')]:
        try:
            v=Decimal(request.GET.get(param,''))
            if v.is_finite() and v>=0: qs=qs.filter(**{field:v})
        except InvalidOperation: pass
    return qs.distinct().order_by('last_name','first_name')

def filter_context():
    return {'subsidiaries':Subsidiary.objects.all(),'domains':ExpertiseDomain.objects.all(),'clusters':Cluster.objects.all(),'skills':Skill.objects.all(),'certifications':Certification.objects.all(),'languages':Language.objects.all()}

@login_required
def expert_list(request):
    return listing(request,expert_filters(request,experts_for(request.user)),'expert_list.html','partials/experts_table.html',title='Référentiel experts',section='expert_list',**filter_context())

@login_required
def matching(request):
    qs=expert_filters(request,experts_for(request.user,matching=True))
    eligible=requests_for(request.user).filter(status__in=['DRAFT','WAITING_MATCHING'])
    selected=get_object_or_404(eligible,pk=request.GET['request_id']) if request.GET.get('request_id','').isdigit() else None
    page=Paginator(qs,12).get_page(request.GET.get('page'))
    required=list(selected.required_skills.all()) if selected else []
    for expert in page.object_list:
        criteria=[]
        if selected:
            if selected.domain_id: criteria.append((selected.domain.name,30,selected.domain_id in {d.pk for d in expert.domains.all()}))
            for skill in required: criteria.append((skill.name,40/len(required),skill.pk in {s.pk for s in expert.skills.all()}))
            if selected.required_language_id: criteria.append((selected.required_language.name,10,selected.required_language_id in {l.pk for l in expert.languages.all()}))
            if selected.max_daily_rate is not None: criteria.append(('Budget',10,expert.daily_rate<=selected.max_daily_rate))
            if selected.desired_start: criteria.append(('Date de disponibilité',10,bool(expert.available_from and expert.available_from<=selected.desired_start)))
        expert.match_score=round(sum(w for label,w,ok in criteria if ok)/sum(w for label,w,ok in criteria)*100) if criteria else None
        expert.match_reasons=[label for label,w,ok in criteria if ok]
    params=request.GET.copy(); params.pop('page',None)
    return render(request,'partials/experts_grid.html' if request.headers.get('HX-Request')=='true' else 'matching.html',dict(page=page,selected_request=selected,eligible_requests=eligible,query=params.urlencode(),title='Matching experts',section='matching',**filter_context()))

@login_required
def expert_detail(request,pk):
    qs=experts_for(request.user)
    if role(request.user) in ('DEMANDEUR','ADMIN_DEMANDEUR'):
        qs=Expert.objects.filter(Q(subsidiary_id=subsidiary_id(request.user))|Q(is_active=True,validation_status='APPROVED')).select_related('subsidiary').prefetch_related('skills','domains','certifications','verticals')
    obj=get_object_or_404(qs,pk=pk)
    return render(request,'expert_detail.html',{'expert':obj,'title':obj.full_name,'section':'expert_list',
      'can_edit':role(request.user)=='ADMIN_OMEA' or (role(request.user)=='ADMIN_FOURNISSEUR' and obj.subsidiary_id==subsidiary_id(request.user)),
      'languages':obj.expertlanguageassignment_set.select_related('language'),'references':obj.references.all(),
      'missions':missions_for(request.user).filter(expert=obj),'evaluations':Evaluation.objects.filter(mission__in=missions_for(request.user),mission__expert=obj).select_related('evaluator'),
      'events':audit_for(request.user).filter(entity_type='Expert',entity_id=str(obj.pk))})

@login_required
def expert_edit(request,pk=None):
    guard(request.user,['ADMIN_FOURNISSEUR','ADMIN_OMEA'])
    obj=get_object_or_404(experts_for(request.user),pk=pk) if pk else None
    form=ExpertForm(request.POST or None,instance=obj,user=request.user)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=form.save(); audit(request.user,'EXPERT_UPDATED',obj,'Profil expert enregistré')
        messages.success(request,'Le profil expert a été enregistré.')
        return redirect('expert_detail',obj.pk)
    return render(request,'form.html',{'form':form,'title':'Modifier le profil' if pk else 'Nouvel expert','section':'expert_list','back_url':'expert_list'})

@login_required
def request_list(request):
    qs=requests_for(request.user); q=request.GET.get('q','')
    if q: qs=qs.filter(Q(reference__icontains=q)|Q(title__icontains=q))
    if request.GET.get('status') in dict(ExpertRequest.STATUSES): qs=qs.filter(status=request.GET['status'])
    for name in ['subsidiary','domain']:
        if request.GET.get(name,'').isdigit(): qs=qs.filter(**{name+'_id':request.GET[name]})
    return listing(request,qs.order_by('-created_at'),'request_list.html','partials/requests_table.html',title='Demandes d’expertise',section='request_list',statuses=ExpertRequest.STATUSES,**filter_context())

@login_required
def request_edit(request,pk=None):
    guard(request.user,['DEMANDEUR','ADMIN_DEMANDEUR','ADMIN_OMEA'])
    obj=get_object_or_404(requests_for(request.user),pk=pk) if pk else None
    if obj and (not request_writable(request.user,obj) or obj.status!='DRAFT'): raise PermissionDenied
    form=ExpertRequestForm(request.POST or None,instance=obj,user=request.user)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=form.save(commit=False); obj.requester=obj.requester if pk else request.user; obj.save(); form.save_m2m()
            audit(request.user,'REQUEST_UPDATED' if pk else 'REQUEST_CREATED',obj,'Demande enregistrée en brouillon')
        messages.success(request,'Brouillon enregistré. Vous pouvez maintenant soumettre votre demande.')
        return redirect('request_detail',obj.pk)
    return render(request,'form.html',{'form':form,'title':'Modifier la demande' if pk else 'Nouvelle demande','section':'request_list','back_url':'request_list'})

@login_required
def request_detail(request,pk):
    obj=get_object_or_404(requests_for(request.user),pk=pk)
    if request.method=='POST':
        if not request_writable(request.user,obj): raise PermissionDenied
        try: obj=submit_request(obj,request.user); messages.success(request,'Demande soumise. Le matching peut commencer.')
        except ValueError as e: messages.error(request,str(e))
        return redirect('request_detail',pk)
    labels=['Demande','Matching','Pré-accord','PO','Mission','PV','Évaluation','Clôture']
    current={'DRAFT':0,'SUBMITTED':1,'WAITING_MATCHING':1,'WAITING_PRE_AGREEMENT':2,'WAITING_PO':3,'IN_PROGRESS':4,'WAITING_EVALUATION':6,'CLOSED':7}.get(obj.status,0)
    return render(request,'request_detail.html',{'item':obj,'title':obj.reference,'section':'request_list','steps':[(label,'done' if i<current else 'current' if i==current else '') for i,label in enumerate(labels)],
      'editable':request_writable(request.user,obj) and obj.status=='DRAFT','events':audit_for(request.user).filter(entity_type='ExpertRequest',entity_id=str(pk)),
      'solicitations':solicitations_for(request.user).filter(request=obj),'documents':obj.documents.all()})

@login_required
def solicitation_list(request):
    qs=solicitations_for(request.user)
    q=request.GET.get('q','')
    if q: qs=qs.filter(Q(request__title__icontains=q)|Q(expert__last_name__icontains=q)|Q(request__reference__icontains=q))
    if request.GET.get('status') in dict(ExpertSolicitation.STATUSES): qs=qs.filter(status=request.GET['status'])
    page=Paginator(qs.order_by('-created_at'),12).get_page(request.GET.get('page'))
    page.object_list=[with_deadline(s) for s in page.object_list]
    params=request.GET.copy(); params.pop('page',None)
    return render(request,'partials/solicitations_table.html' if request.headers.get('HX-Request')=='true' else 'solicitation_list.html',{'page':page,'query':params.urlencode(),'title':'Sollicitations','section':'solicitation_list','statuses':ExpertSolicitation.STATUSES})

@login_required
def solicitation_detail(request,pk):
    s=get_object_or_404(solicitations_for(request.user),pk=pk)
    can_respond=role(request.user)=='ADMIN_FOURNISSEUR' and s.expert.subsidiary_id==subsidiary_id(request.user) and s.status=='PENDING' and s.deadline>timezone.now()
    if request.method=='POST':
        if not can_respond: raise PermissionDenied
        try:
            if request.POST.get('action')=='accept': accept_solicitation(s,request.user)
            else: refuse_solicitation(s,request.user,request.POST.get('reason',''))
            messages.success(request,'Votre réponse a été enregistrée.')
        except ValueError as e: messages.error(request,str(e))
        return redirect('solicitation_detail',pk)
    return render(request,'solicitation_detail.html',{'item':with_deadline(s),'can_respond':can_respond,'title':'Pré-accord fournisseur','section':'solicitation_list','events':audit_for(request.user).filter(entity_type='ExpertSolicitation',entity_id=str(pk))})

@login_required
def solicitation_create(request,expert_id):
    guard(request.user,['ADMIN_DEMANDEUR','ADMIN_OMEA'])
    expert=get_object_or_404(experts_for(request.user,matching=True),pk=expert_id)
    eligible=requests_for(request.user).filter(status='WAITING_MATCHING')
    if request.method=='POST':
        obj=get_object_or_404(eligible,pk=request.POST.get('request_id'))
        with transaction.atomic():
            expert=Expert.objects.select_for_update().get(pk=expert.pk)
            s=create_solicitation(obj,expert,request.user)
        messages.success(request,'Sollicitation créée. Le fournisseur dispose de 48 heures.')
        response=redirect('solicitation_detail',s.pk)
        if request.headers.get('HX-Request')=='true':
            response=HttpResponse(); response['HX-Redirect']=redirect('solicitation_detail',s.pk).url
        return response
    return render(request,'partials/solicitation_form.html' if request.headers.get('HX-Request')=='true' else 'solicitation_create.html',{'expert':expert,'eligible':eligible,'title':'Solliciter un expert','section':'matching'})

@login_required
def mission_list(request):
    qs=missions_for(request.user)
    if request.GET.get('q'): qs=qs.filter(request__title__icontains=request.GET['q'])
    return listing(request,qs.order_by('-start_date'),'mission_list.html','partials/missions_table.html',title='Missions',section='mission_list')

@login_required
def mission_detail(request,pk):
    obj=get_object_or_404(missions_for(request.user),pk=pk)
    return render(request,'mission_detail.html',{'item':obj,'title':obj.request.title,'section':'mission_list','events':audit_for(request.user).filter(entity_type='Mission',entity_id=str(pk))})

@login_required
def notifications(request):
    qs=request.user.notifications.order_by('-created_at')
    if request.GET.get('unread')=='1': qs=qs.filter(is_read=False)
    return listing(request,qs,'notifications.html','partials/notifications_list.html',title='Notifications',section='notifications')

@login_required
def notification_preview(request):
    return render(request,'partials/notifications_dropdown.html',{'items':request.user.notifications.order_by('-created_at')[:5]})

@login_required
@require_POST
def mark_notification_read(request,pk):
    n=get_object_or_404(Notification,pk=pk,user=request.user)
    n.is_read=True; n.save(update_fields=['is_read'])
    if request.headers.get('HX-Request')=='true':
        response=notifications(request); response['HX-Trigger']='notificationsChanged'; return response
    return redirect('notifications')

@login_required
def audit_list(request):
    qs=audit_for(request.user)
    if request.GET.get('q'): qs=qs.filter(Q(description__icontains=request.GET['q'])|Q(action__icontains=request.GET['q']))
    return listing(request,qs,'audit_list.html','partials/audit_timeline.html',title='Journal d’activité',section='audit_list')

@login_required
def reports(request):
    reqs=requests_for(request.user); ex=experts_for(request.user); sols=solicitations_for(request.user)
    total=sols.filter(status__in=['ACCEPTED','REFUSED']).count()
    rate=round(sols.filter(status='ACCEPTED').count()/total*100) if total else None
    return render(request,'reports.html',{'title':'Reporting & indicateurs','section':'reports','acceptance':rate,
      'average':ex.aggregate(value=Avg('average_score'))['value'],'by_status':[dict(label=dict(ExpertRequest.STATUSES).get(row['status'],row['status']),total=row['total']) for row in reqs.values('status').annotate(total=Count('id'))],
      'by_subsidiary':ex.values('subsidiary__name').annotate(total=Count('id')),'mission_count':missions_for(request.user).count(),'total_experts':ex.count()})

@login_required
def functional_admin(request):
    guard(request.user,['ADMIN_OMEA'])
    return render(request,'functional_admin.html',{'title':'Administration fonctionnelle','section':'functional_admin','subsidiaries':Subsidiary.objects.select_related('cluster'),'profiles':Profile.objects.select_related('user','subsidiary'),'domains':ExpertiseDomain.objects.annotate(total=Count('expert'))})
