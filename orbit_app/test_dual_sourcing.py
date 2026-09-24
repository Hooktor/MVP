from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Cluster, Expert, ExpertRequest, ExpertSolicitation, Profile, Subsidiary
from .selectors import requests_for, solicitations_for
from .services import create_broadcast_proposal, submit_request


class DualSourcingWorkflowTests(TestCase):
    def setUp(self):
        cluster=Cluster.objects.create(name='Dual sourcing')
        self.request_subsidiary=Subsidiary.objects.create(name='Orange Morocco',code='MA',cluster=cluster)
        self.expert_subsidiary=Subsidiary.objects.create(name='Orange Tunisia',code='TN',cluster=cluster)
        self.requester=User.objects.create_user('requester',password='x')
        self.responder=User.objects.create_user('responder',password='x')
        Profile.objects.create(user=self.requester,role='ADMIN_FILIALE',subsidiary=self.request_subsidiary)
        Profile.objects.create(user=self.responder,role='ADMIN_FILIALE',subsidiary=self.expert_subsidiary)
        self.expert=Expert.objects.create(first_name='Leila',last_name='Ben Ali',employee_id='TN-42',job_title='Cloud architect',subsidiary=self.expert_subsidiary,validation_status='APPROVED',availability='AVAILABLE')

    def create_request(self,mode,target=None):
        return ExpertRequest.objects.create(title='Modernisation cloud',description='Besoin de renfort',requester=self.requester,subsidiary=self.request_subsidiary,mode=mode,target_expert=target,duration_days=10)

    def test_direct_request_creates_one_pre_agreement_for_target_expert(self):
        request=self.create_request('DIRECT',self.expert)
        submit_request(request,self.requester)
        request.refresh_from_db(); self.expert.refresh_from_db()
        self.assertEqual(request.status,'WAITING_PRE_AGREEMENT')
        self.assertEqual(self.expert.availability,'PRE_AGREEMENT')
        self.assertEqual(ExpertSolicitation.objects.filter(request=request,expert=self.expert).count(),1)
        self.assertTrue(solicitations_for(self.responder).filter(request=request).exists())

    def test_broadcast_is_visible_to_other_affiliate_and_accepts_a_proposal(self):
        request=self.create_request('BROADCAST')
        submit_request(request,self.requester)
        self.assertTrue(requests_for(self.responder).filter(pk=request.pk).exists())
        proposal=create_broadcast_proposal(request,self.expert,self.responder)
        self.assertEqual(proposal.request_id,request.pk)
        self.assertEqual(proposal.expert_id,self.expert.pk)
        self.assertEqual(request.proposals.count(),1)
