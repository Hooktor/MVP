from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Cluster(models.Model):
    name=models.CharField(max_length=120,unique=True)
    def __str__(self): return self.name
class Subsidiary(models.Model):
    name=models.CharField(max_length=160); code=models.CharField(max_length=20,unique=True); cluster=models.ForeignKey(Cluster,on_delete=models.PROTECT,related_name='subsidiaries')
    def __str__(self): return self.name
class Profile(models.Model):
    ROLE_CHOICES=[('DEMANDEUR','Demandeur'),('ADMIN_DEMANDEUR','Administrateur demandeur'),('ADMIN_FOURNISSEUR','Administrateur fournisseur'),('ADMIN_OMEA','Administrateur OMEA')]
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile'); role=models.CharField(max_length=30,choices=ROLE_CHOICES,default='DEMANDEUR'); subsidiary=models.ForeignKey(Subsidiary,null=True,blank=True,on_delete=models.PROTECT,related_name='profiles')
    def __str__(self): return self.user.get_username()
class ExpertiseDomain(models.Model):
    name=models.CharField(max_length=120,unique=True)
    def __str__(self): return self.name
class Skill(models.Model):
    name=models.CharField(max_length=120,unique=True)
    domain=models.ForeignKey(ExpertiseDomain,on_delete=models.PROTECT,related_name='skills')
    def __str__(self): return self.name
class Certification(models.Model):
    name=models.CharField(max_length=160,unique=True)
    issuer=models.CharField(max_length=160,blank=True)
    def __str__(self): return self.name
class BusinessVertical(models.Model):
    name=models.CharField(max_length=120,unique=True)
    def __str__(self): return self.name
class Language(models.Model):
    name=models.CharField(max_length=80,unique=True)
    def __str__(self): return self.name
class Expert(models.Model):
    AVAILABILITY=[('AVAILABLE','Disponible'),('PRE_AGREEMENT','Pré-accord'),('ON_MISSION','En mission'),('UNAVAILABLE','Indisponible')]; VALIDATION=[('DRAFT','Brouillon'),('SUBMITTED','Soumis'),('APPROVED','Approuvé'),('REJECTED','Rejeté')]
    first_name=models.CharField(max_length=100); last_name=models.CharField(max_length=100); employee_id=models.CharField(max_length=60,unique=True); job_title=models.CharField(max_length=160); subsidiary=models.ForeignKey(Subsidiary,on_delete=models.PROTECT,related_name='experts'); domains=models.ManyToManyField(ExpertiseDomain,blank=True); skills=models.ManyToManyField(Skill,blank=True); certifications=models.ManyToManyField(Certification,blank=True); verticals=models.ManyToManyField(BusinessVertical,blank=True); languages=models.ManyToManyField(Language,through='ExpertLanguageAssignment',blank=True); daily_rate=models.DecimalField(max_digits=10,decimal_places=2,default=0); currency=models.CharField(max_length=3,default='EUR'); availability=models.CharField(max_length=20,choices=AVAILABILITY,default='AVAILABLE'); validation_status=models.CharField(max_length=20,choices=VALIDATION,default='DRAFT'); average_score=models.DecimalField(max_digits=3,decimal_places=2,default=0); available_from=models.DateField(null=True,blank=True); bio=models.TextField(blank=True); is_active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.first_name} {self.last_name} ({self.employee_id})'
    @property
    def full_name(self): return f'{self.first_name} {self.last_name}'
    @property
    def completeness(self):
        fields=[self.first_name,self.last_name,self.employee_id,self.job_title,self.bio,self.available_from,self.daily_rate]; return round(sum(bool(x) for x in fields)/len(fields)*100)
class ExpertLanguageAssignment(models.Model):
    LEVELS=[('A1','A1'),('A2','A2'),('B1','B1'),('B2','B2'),('C1','C1'),('C2','C2')]
    expert=models.ForeignKey(Expert,on_delete=models.CASCADE); language=models.ForeignKey(Language,on_delete=models.PROTECT); level=models.CharField(max_length=2,choices=LEVELS)
    class Meta: constraints=[models.UniqueConstraint(fields=['expert','language'],name='unique_expert_language')]
class ProjectReference(models.Model): expert=models.ForeignKey(Expert,on_delete=models.CASCADE,related_name='references'); title=models.CharField(max_length=200); description=models.TextField(); client=models.CharField(max_length=160,blank=True); year=models.PositiveIntegerField(null=True,blank=True)
class ExpertRequest(models.Model):
    STATUSES=[('DRAFT','Brouillon'),('SUBMITTED','Soumise'),('WAITING_MATCHING','Matching'),('WAITING_PRE_AGREEMENT','Pré-accord'),('WAITING_PO','PO attendu'),('IN_PROGRESS','En cours'),('WAITING_EVALUATION','Évaluation'),('CLOSED','Clôturée'),('CANCELLED','Annulée')]
    reference=models.CharField(max_length=20,unique=True,blank=True); title=models.CharField(max_length=200); description=models.TextField(); requester=models.ForeignKey(User,on_delete=models.PROTECT,related_name='requests'); subsidiary=models.ForeignKey(Subsidiary,on_delete=models.PROTECT,related_name='requests'); domain=models.ForeignKey(ExpertiseDomain,null=True,blank=True,on_delete=models.PROTECT); required_skills=models.ManyToManyField(Skill,blank=True); required_language=models.ForeignKey(Language,null=True,blank=True,on_delete=models.PROTECT); min_language_level=models.CharField(max_length=2,blank=True); max_daily_rate=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True); desired_start=models.DateField(null=True,blank=True); duration_days=models.PositiveIntegerField(default=1); status=models.CharField(max_length=30,choices=STATUSES,default='DRAFT'); created_at=models.DateTimeField(auto_now_add=True); submitted_at=models.DateTimeField(null=True,blank=True)
    def save(self,*args,**kwargs):
        if not self.reference:
            year=timezone.now().year; last=ExpertRequest.objects.filter(reference__startswith=f'REQ-{year}-').order_by('-reference').first(); n=int(last.reference[-4:])+1 if last else 1; self.reference=f'REQ-{year}-{n:04d}'
        super().save(*args,**kwargs)
class RequestDocument(models.Model): TYPES=[('RFP','RFP'),('RFI','RFI'),('EOI','EOI'),('OTHER','Autre')]; request=models.ForeignKey(ExpertRequest,on_delete=models.CASCADE,related_name='documents'); file=models.FileField(upload_to='requests/%Y/%m/'); original_name=models.CharField(max_length=255); document_type=models.CharField(max_length=10,choices=TYPES); uploaded_by=models.ForeignKey(User,on_delete=models.PROTECT); uploaded_at=models.DateTimeField(auto_now_add=True)
class ExpertSolicitation(models.Model):
    STATUSES=[('PENDING','En attente'),('ACCEPTED','Acceptée'),('REFUSED','Refusée'),('EXPIRED','Expirée'),('ESCALATED','Escaladée'),('CANCELLED','Annulée')]
    request=models.ForeignKey(ExpertRequest,on_delete=models.CASCADE,related_name='solicitations'); expert=models.ForeignKey(Expert,on_delete=models.PROTECT,related_name='solicitations'); created_by=models.ForeignKey(User,on_delete=models.PROTECT); status=models.CharField(max_length=15,choices=STATUSES,default='PENDING'); deadline=models.DateTimeField(); response_reason=models.TextField(blank=True); responded_at=models.DateTimeField(null=True,blank=True); reminders_sent=models.JSONField(default=dict); created_at=models.DateTimeField(auto_now_add=True)
class Mission(models.Model):
    STATUS=[('PLANNED','Planifiée'),('IN_PROGRESS','En cours'),('COMPLETED','Terminée'),('CANCELLED','Annulée')]; request=models.OneToOneField(ExpertRequest,on_delete=models.PROTECT,related_name='mission'); expert=models.ForeignKey(Expert,on_delete=models.PROTECT,related_name='missions'); supplier_subsidiary=models.ForeignKey(Subsidiary,on_delete=models.PROTECT); start_date=models.DateField(); planned_end_date=models.DateField(); actual_end_date=models.DateField(null=True,blank=True); status=models.CharField(max_length=20,choices=STATUS,default='PLANNED'); po_document=models.ForeignKey('TransactionDocument',null=True,blank=True,on_delete=models.PROTECT,related_name='po_missions'); pv_document=models.ForeignKey('TransactionDocument',null=True,blank=True,on_delete=models.PROTECT,related_name='pv_missions')
class TransactionDocument(models.Model): TYPES=[('PO','Bon de commande'),('PV','Procès-verbal')]; request=models.ForeignKey(ExpertRequest,on_delete=models.CASCADE,related_name='transaction_documents'); file=models.FileField(upload_to='transactions/%Y/%m/'); original_name=models.CharField(max_length=255); document_type=models.CharField(max_length=2,choices=TYPES); uploaded_by=models.ForeignKey(User,on_delete=models.PROTECT); uploaded_at=models.DateTimeField(auto_now_add=True)
class Evaluation(models.Model): mission=models.OneToOneField(Mission,on_delete=models.PROTECT,related_name='evaluation'); evaluator=models.ForeignKey(User,on_delete=models.PROTECT); rating=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)]); comment=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
class Notification(models.Model): user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications'); title=models.CharField(max_length=200); message=models.TextField(); url=models.CharField(max_length=300,blank=True); is_read=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
class AuditEvent(models.Model): actor=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL); action=models.CharField(max_length=100); entity_type=models.CharField(max_length=100); entity_id=models.CharField(max_length=80); description=models.TextField(); old_status=models.CharField(max_length=40,blank=True); new_status=models.CharField(max_length=40,blank=True); metadata=models.JSONField(default=dict); ip_address=models.GenericIPAddressField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
