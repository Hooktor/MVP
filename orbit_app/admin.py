from django.contrib import admin
from .models import *
for m in [Cluster,Subsidiary,Profile,ExpertiseDomain,Skill,Certification,BusinessVertical,Language,Expert,ExpertLanguageAssignment,ProjectReference,ExpertRequest,RequestDocument,ExpertSolicitation,Mission,TransactionDocument,Evaluation,Notification,AuditEvent]: admin.site.register(m)
