from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from .models import *

class EnterpriseInterfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cluster=Cluster.objects.create(name='QA')
        cls.sub=Subsidiary.objects.create(name='Filiale A',code='QA-A',cluster=cluster)
        cls.other=Subsidiary.objects.create(name='Filiale B',code='QA-B',cluster=cluster)
        cls.users={}
        for role in ['DEMANDEUR','ADMIN_DEMANDEUR','ADMIN_FOURNISSEUR','ADMIN_OMEA']:
            u=User.objects.create_user(role,password='test-password')
            Profile.objects.create(user=u,role=role,subsidiary=cls.sub)
            cls.users[role]=u
        cls.expert=Expert.objects.create(first_name='Amina',last_name='Test',employee_id='QA1',job_title='Cloud architect',subsidiary=cls.sub,validation_status='APPROVED')
        cls.req=ExpertRequest.objects.create(title='Migration Cloud',description='Mission test',requester=cls.users['DEMANDEUR'],subsidiary=cls.sub)
        cls.hidden=ExpertRequest.objects.create(title='Secret filiale B',description='Privé',requester=cls.users['ADMIN_OMEA'],subsidiary=cls.other)
        cls.sol=ExpertSolicitation.objects.create(request=cls.req,expert=cls.expert,created_by=cls.users['ADMIN_DEMANDEUR'],deadline=timezone.now()+timedelta(hours=48))
        cls.mission=Mission.objects.create(request=cls.req,expert=cls.expert,supplier_subsidiary=cls.sub,start_date=timezone.now().date(),planned_end_date=timezone.now().date()+timedelta(days=10))

    def test_all_role_pages_render_and_local_assets(self):
        for role,user in self.users.items():
            self.client.force_login(user)
            for name in ['dashboard','request_list','expert_list','matching','solicitation_list','mission_list','notifications','reports','audit_list']:
                response=self.client.get(reverse(name))
                self.assertEqual(response.status_code,200,(role,name))
                self.assertNotContains(response,'cdn.jsdelivr.net')
                self.assertContains(response,'vendor/htmx/htmx.min.js')
            self.assertEqual(self.client.get(reverse('functional_admin')).status_code,200 if role=='ADMIN_OMEA' else 403)

    def test_detail_and_form_screens_render(self):
        self.client.force_login(self.users['ADMIN_OMEA'])
        for name,pk in [('request_detail',self.req.pk),('expert_detail',self.expert.pk),('solicitation_detail',self.sol.pk),('mission_detail',self.mission.pk),('request_edit',self.req.pk),('expert_edit',self.expert.pk)]:
            self.assertEqual(self.client.get(reverse(name,args=[pk])).status_code,200,name)
        for name in ['request_create','expert_create','notification_preview']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200,name)

    def test_htmx_filters_return_fragments(self):
        self.client.force_login(self.users['ADMIN_DEMANDEUR'])
        for name in ['request_list','expert_list','matching','solicitation_list','mission_list','audit_list','notifications']:
            response=self.client.get(reverse(name),{'q':'nothing-matches'},HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code,200,name)
            self.assertNotContains(response,'<!doctype')
        response=self.client.get(reverse('request_list'),{'q':'Migration'},HTTP_HX_REQUEST='true')
        self.assertContains(response,'Migration Cloud')
        self.assertNotContains(response,'Secret filiale B')

    def test_foreign_requests_and_write_roles(self):
        self.client.force_login(self.users['ADMIN_DEMANDEUR'])
        self.assertEqual(self.client.get(reverse('request_detail',args=[self.hidden.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('expert_create')).status_code,403)
        self.client.force_login(self.users['ADMIN_FOURNISSEUR'])
        self.assertEqual(self.client.get(reverse('request_create')).status_code,403)

    def test_read_notification_is_post_and_owned(self):
        n=Notification.objects.create(user=self.users['DEMANDEUR'],title='Test',message='Test')
        self.client.force_login(self.users['DEMANDEUR'])
        url=reverse('mark_notification_read',args=[n.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url,HTTP_HX_REQUEST='true').status_code,200)
        n.refresh_from_db(); self.assertTrue(n.is_read)
        self.client.force_login(self.users['ADMIN_DEMANDEUR'])
        self.assertEqual(self.client.post(url).status_code,404)

    def test_csrf_enforced_and_closed_request_not_editable(self):
        c=Client(enforce_csrf_checks=True); c.force_login(self.users['ADMIN_DEMANDEUR'])
        self.assertEqual(c.post(reverse('request_detail',args=[self.req.pk])).status_code,403)
        self.req.status='CLOSED'; self.req.save()
        self.client.force_login(self.users['ADMIN_OMEA'])
        self.assertEqual(self.client.get(reverse('request_edit',args=[self.req.pk])).status_code,403)

    def test_matching_excludes_unapproved_and_busy(self):
        self.client.force_login(self.users['ADMIN_DEMANDEUR'])
        self.assertContains(self.client.get(reverse('matching')),'Amina')
        self.expert.availability='ON_MISSION';self.expert.save()
        self.assertNotContains(self.client.get(reverse('matching')),'Amina')
        self.expert.availability='AVAILABLE';self.expert.validation_status='DRAFT';self.expert.save()
        self.assertNotContains(self.client.get(reverse('matching')),'Amina')

    def test_login_is_custom(self):
        self.assertContains(self.client.get(reverse('login')),'L’expertise se partage')

