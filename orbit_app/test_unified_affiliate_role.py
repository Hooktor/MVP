from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Cluster, Subsidiary, Profile, ExpertiseDomain, Skill, Expert, ExpertRequest, ExpertSolicitation
from .services import submit_request


class UnifiedAffiliateRoleTests(TestCase):
    def setUp(self):
        cluster=Cluster.objects.create(name='Inter-filiales')
        self.requesting_sub=Subsidiary.objects.create(name='Filiale demandeuse',code='REQ',cluster=cluster)
        self.expert_sub=Subsidiary.objects.create(name='Filiale experte',code='EXP',cluster=cluster)
        self.requesting_admin=User.objects.create_user('admin-requesting',password='x')
        self.expert_admin=User.objects.create_user('admin-expert',password='x')
        Profile.objects.create(user=self.requesting_admin,role='ADMIN_FILIALE',subsidiary=self.requesting_sub)
        Profile.objects.create(user=self.expert_admin,role='ADMIN_FILIALE',subsidiary=self.expert_sub)
        self.domain=ExpertiseDomain.objects.create(name='Architecture')
        self.skill=Skill.objects.create(name='Cloud',domain=self.domain)
        self.expert=Expert.objects.create(first_name='Aya',last_name='Expert',employee_id='EXP-ROLE-1',job_title='Architecte',subsidiary=self.expert_sub,validation_status='APPROVED',availability='AVAILABLE')
        self.expert.domains.add(self.domain); self.expert.skills.add(self.skill)

    def test_each_affiliate_admin_can_issue_and_receive_solicitations(self):
        request=ExpertRequest.objects.create(title='Besoin inter-filiale',description='Recherche expertise Cloud',requester=self.requesting_admin,subsidiary=self.requesting_sub,domain=self.domain)
        request.required_skills.add(self.skill); submit_request(request,self.requesting_admin)
        self.client.force_login(self.requesting_admin)
        self.assertEqual(self.client.get(reverse('expert_list')).status_code,200)
        response=self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk})
        self.assertEqual(response.status_code,302)
        solicitation=ExpertSolicitation.objects.get(request=request)
        self.assertContains(self.client.get(reverse('solicitation_list')),request.reference)
        self.client.force_login(self.expert_admin)
        listing=self.client.get(reverse('solicitation_list'))
        self.assertContains(listing,request.reference)
        accepted=self.client.post(reverse('solicitation_detail',args=[solicitation.pk]),{'action':'accept'})
        self.assertEqual(accepted.status_code,302)
        solicitation.refresh_from_db(); self.assertEqual(solicitation.status,'ACCEPTED')

    def test_affiliate_admin_can_create_a_request_and_manage_own_experts(self):
        self.client.force_login(self.expert_admin)
        create_request=self.client.post(reverse('request_create'),{'title':'Besoin de ma filiale','description':'Un besoin valide','subsidiary':self.expert_sub.pk,'domain':self.domain.pk,'duration_days':5})
        self.assertEqual(create_request.status_code,302)
        self.assertTrue(ExpertRequest.objects.filter(subsidiary=self.expert_sub,title='Besoin de ma filiale').exists())
        self.assertEqual(self.client.get(reverse('expert_edit',args=[self.expert.pk])).status_code,200)

    def test_direct_solicitation_needs_no_existing_request_then_creates_mission_file_after_acceptance(self):
        self.client.force_login(self.requesting_admin)
        response=self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{
            'subject':'Renfort cloud urgent','message':'Besoin ponctuel pour un projet client.',
            'duration_days':10,'desired_start':'2026-10-01','max_daily_rate':'650',
        })
        self.assertEqual(response.status_code,302)
        solicitation=ExpertSolicitation.objects.get(subject='Renfort cloud urgent')
        self.assertIsNone(solicitation.request_id)
        self.assertEqual(self.client.get(reverse('solicitation_detail',args=[solicitation.pk])).status_code,200)
        self.client.force_login(self.expert_admin)
        self.client.post(reverse('solicitation_detail',args=[solicitation.pk]),{'action':'accept'})
        solicitation.refresh_from_db(); self.assertEqual(solicitation.status,'ACCEPTED')
        self.assertEqual(solicitation.request.status,'WAITING_PO')
        self.assertEqual(solicitation.request.target_expert,self.expert)
