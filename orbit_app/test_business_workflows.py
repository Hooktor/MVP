from datetime import timedelta
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import *
from .services import create_evaluation, process_timeouts, register_delivery_report, register_purchase_order, submit_request

class BusinessWorkflowHttpTests(TestCase):
    def setUp(self):
        cluster=Cluster.objects.create(name='Workflow')
        self.sub=Subsidiary.objects.create(name='Workflow Senegal',code='WF',cluster=cluster)
        self.requester=User.objects.create_user('wf-requester',password='x')
        self.admin=User.objects.create_user('wf-admin',password='x')
        self.supplier=User.objects.create_user('wf-supplier',password='x')
        self.omea=User.objects.create_user('wf-omea',password='x')
        Profile.objects.create(user=self.requester,role='DEMANDEUR',subsidiary=self.sub)
        Profile.objects.create(user=self.admin,role='ADMIN_DEMANDEUR',subsidiary=self.sub)
        Profile.objects.create(user=self.supplier,role='ADMIN_FOURNISSEUR',subsidiary=self.sub)
        Profile.objects.create(user=self.omea,role='ADMIN_OMEA',subsidiary=self.sub)
        self.domain=ExpertiseDomain.objects.create(name='Cloud')
        self.skill=Skill.objects.create(name='Kubernetes',domain=self.domain)
        self.expert=Expert.objects.create(first_name='Nora',last_name='Expert',employee_id='WF-1',job_title='Cloud Architect',subsidiary=self.sub,validation_status='APPROVED',availability='AVAILABLE',daily_rate=600,available_from=timezone.localdate())
        self.expert.domains.add(self.domain); self.expert.skills.add(self.skill)

    def create_request(self):
        return ExpertRequest.objects.create(title='Modernisation cloud',description='Accompagnement de la migration',requester=self.requester,subsidiary=self.sub,domain=self.domain,max_daily_rate=700,desired_start=timezone.localdate()+timedelta(days=7))

    def test_requester_creates_draft_and_submits_through_views(self):
        self.client.force_login(self.requester)
        create=self.client.post(reverse('request_create'),{'title':'Nouveau besoin','description':'Un besoin précis','subsidiary':self.sub.pk,'domain':self.domain.pk,'required_skills':[self.skill.pk],'duration_days':12})
        self.assertEqual(create.status_code,302)
        request=ExpertRequest.objects.get(title='Nouveau besoin')
        self.assertEqual(request.status,'DRAFT')
        submit=self.client.post(reverse('request_detail',args=[request.pk]))
        self.assertEqual(submit.status_code,302)
        request.refresh_from_db(); self.assertEqual(request.status,'WAITING_MATCHING')
        self.assertTrue(AuditEvent.objects.filter(entity_id=str(request.pk),action='SUBMIT_REQUEST').exists())

    def test_matching_score_and_htmx_solicitation_creation(self):
        request=self.create_request(); request.required_skills.add(self.skill); submit_request(request,self.requester)
        self.client.force_login(self.admin)
        matching=self.client.get(reverse('matching'),{'request_id':request.pk})
        self.assertContains(matching,'Correspondance')
        self.assertContains(matching,'100 %')
        response=self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk},HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code,200)
        self.assertIn('HX-Redirect',response.headers)
        solicitation=ExpertSolicitation.objects.get(request=request)
        self.assertEqual(solicitation.status,'PENDING')
        self.expert.refresh_from_db(); request.refresh_from_db()
        self.assertEqual(self.expert.availability,'PRE_AGREEMENT')
        self.assertEqual(request.status,'WAITING_PRE_AGREEMENT')

    def test_supplier_accepts_and_refuses_through_views(self):
        request=self.create_request(); submit_request(request,self.requester)
        self.client.force_login(self.admin)
        self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk})
        solicitation=ExpertSolicitation.objects.get(request=request)
        self.client.force_login(self.supplier)
        accepted=self.client.post(reverse('solicitation_detail',args=[solicitation.pk]),{'action':'accept'})
        self.assertEqual(accepted.status_code,302)
        solicitation.refresh_from_db(); request.refresh_from_db()
        self.assertEqual(solicitation.status,'ACCEPTED'); self.assertEqual(request.status,'WAITING_PO')
        self.expert.availability='AVAILABLE'; self.expert.save(update_fields=['availability'])
        request2=self.create_request(); submit_request(request2,self.requester)
        self.client.force_login(self.admin)
        self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request2.pk})
        refused=ExpertSolicitation.objects.get(request=request2)
        self.client.force_login(self.supplier)
        response=self.client.post(reverse('solicitation_detail',args=[refused.pk]),{'action':'refuse','reason':'Capacité déjà engagée'})
        self.assertEqual(response.status_code,302)
        refused.refresh_from_db(); request2.refresh_from_db(); self.expert.refresh_from_db()
        self.assertEqual(refused.status,'REFUSED'); self.assertEqual(request2.status,'WAITING_MATCHING'); self.assertEqual(self.expert.availability,'AVAILABLE')

    def test_timeout_is_idempotent_and_releases_expert(self):
        request=self.create_request(); submit_request(request,self.requester)
        self.client.force_login(self.admin)
        self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk})
        solicitation=ExpertSolicitation.objects.get(request=request)
        solicitation.deadline=timezone.now()-timedelta(minutes=1); solicitation.save(update_fields=['deadline'])
        self.assertEqual(process_timeouts(),1)
        self.assertEqual(process_timeouts(),0)
        solicitation.refresh_from_db(); request.refresh_from_db(); self.expert.refresh_from_db()
        self.assertEqual(solicitation.status,'ESCALATED'); self.assertEqual(request.status,'WAITING_MATCHING'); self.assertEqual(self.expert.availability,'AVAILABLE')

    def test_requester_uploads_a_pdf_po_and_mission_is_planned(self):
        request=self.create_request(); submit_request(request,self.requester)
        self.client.force_login(self.admin)
        self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk})
        solicitation=ExpertSolicitation.objects.get(request=request)
        from .services import accept_solicitation
        accept_solicitation(solicitation,self.supplier)
        po=SimpleUploadedFile('PO-ORBIT.pdf',b'%PDF-1.4 bon de commande',content_type='application/pdf')
        mission=register_purchase_order(request,po,self.requester)
        request.refresh_from_db(); self.expert.refresh_from_db()
        self.assertEqual(request.status,'IN_PROGRESS'); self.assertEqual(mission.po_document.document_type,'PO')
        self.assertEqual(self.expert.availability,'ON_MISSION')

    def test_supplier_uploads_a_pdf_pv_and_request_moves_to_evaluation(self):
        request=self.create_request(); submit_request(request,self.requester)
        self.client.force_login(self.admin); self.client.post(reverse('solicitation_create',args=[self.expert.pk]),{'request_id':request.pk})
        solicitation=ExpertSolicitation.objects.get(request=request)
        from .services import accept_solicitation
        accept_solicitation(solicitation,self.supplier)
        mission=register_purchase_order(request,SimpleUploadedFile('PO.pdf',b'%PDF-1.4',content_type='application/pdf'),self.requester)
        register_delivery_report(mission,SimpleUploadedFile('PV.pdf',b'%PDF-1.4',content_type='application/pdf'),self.supplier)
        mission.refresh_from_db(); request.refresh_from_db()
        self.assertEqual(mission.pv_document.document_type,'PV'); self.assertEqual(request.status,'WAITING_EVALUATION')

    def test_evaluation_closes_mission_and_recalculates_score(self):
        request=self.create_request(); request.status='WAITING_EVALUATION'; request.save(update_fields=['status'])
        mission=Mission.objects.create(request=request,expert=self.expert,supplier_subsidiary=self.sub,start_date=timezone.localdate()-timedelta(days=6),planned_end_date=timezone.localdate(),status='IN_PROGRESS')
        evaluation=create_evaluation(mission,self.requester,5,'Livrable conforme et très bon accompagnement.')
        mission.refresh_from_db(); request.refresh_from_db(); self.expert.refresh_from_db()
        self.assertEqual(evaluation.rating,5); self.assertEqual(mission.status,'COMPLETED'); self.assertEqual(request.status,'CLOSED'); self.assertEqual(self.expert.availability,'AVAILABLE'); self.assertEqual(self.expert.average_score,5)
