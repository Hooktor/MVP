from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import *
from .services import *

class OrbitWorkflowTests(TestCase):
    def setUp(self):
        self.cluster=Cluster.objects.create(name='Sonatel'); self.sub=Subsidiary.objects.create(name='Sonatel SN',code='SN',cluster=self.cluster); self.other=Subsidiary.objects.create(name='OCI CI',code='CI',cluster=self.cluster)
        self.user=User.objects.create_user('requester',password='x'); Profile.objects.create(user=self.user,role='ADMIN_DEMANDEUR',subsidiary=self.sub)
        self.supplier=User.objects.create_user('supplier',password='x'); Profile.objects.create(user=self.supplier,role='ADMIN_FOURNISSEUR',subsidiary=self.sub)
        self.domain=ExpertiseDomain.objects.create(name='Data'); self.expert=Expert.objects.create(first_name='A',last_name='B',employee_id='E1',job_title='Engineer',subsidiary=self.sub,validation_status='APPROVED',availability='AVAILABLE')
        self.request=ExpertRequest.objects.create(title='Besoin',description='D',requester=self.user,subsidiary=self.sub)
    def test_reference_and_submit(self):
        self.assertRegex(self.request.reference,r'^REQ-\d{4}-\d{4}$'); submit_request(self.request,self.user); self.assertEqual(self.request.refresh_from_db() or self.request.status,'WAITING_MATCHING'); self.assertEqual(AuditEvent.objects.count(),1)
    def test_solicitation_acceptance_requires_supplier_scope(self):
        submit_request(self.request,self.user); s=create_solicitation(self.request,self.expert,self.user); self.assertEqual(s.expert.availability,'PRE_AGREEMENT'); accept_solicitation(s,self.supplier); self.request.refresh_from_db(); self.assertEqual(self.request.status,'WAITING_PO'); self.assertTrue(Notification.objects.filter(user=self.user).exists())
    def test_refusal_requires_reason_and_releases(self):
        submit_request(self.request,self.user); s=create_solicitation(self.request,self.expert,self.user)
        with self.assertRaises(ValueError): refuse_solicitation(s,self.supplier,' ')
        refuse_solicitation(s,self.supplier,'Indisponible'); self.expert.refresh_from_db(); self.assertEqual(self.expert.availability,'AVAILABLE')
    def test_timeout_escalates(self):
        submit_request(self.request,self.user); s=create_solicitation(self.request,self.expert,self.user); s.deadline=timezone.now()-timedelta(hours=1); s.save(update_fields=['deadline']); self.assertEqual(process_timeouts(),1); s.refresh_from_db(); self.assertEqual(s.status,'ESCALATED')
    def test_cross_subsidiary_supplier_cannot_accept(self):
        other=User.objects.create_user('other',password='x'); Profile.objects.create(user=other,role='ADMIN_FOURNISSEUR',subsidiary=self.other); submit_request(self.request,self.user); s=create_solicitation(self.request,self.expert,self.user)
        with self.assertRaises(ValueError): accept_solicitation(s,other)
