from datetime import date
from io import BytesIO
from openpyxl import Workbook
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from .models import AuditEvent, Cluster, Expert, Profile, Subsidiary
from .views import IMPORT_HEADERS


class ExpertImportTests(TestCase):
    def setUp(self):
        cluster=Cluster.objects.create(name='Import cluster')
        self.sub=Subsidiary.objects.create(name='Import Senegal',code='IMP',cluster=cluster)
        self.other=Subsidiary.objects.create(name='Import Mali',code='MAL',cluster=cluster)
        self.supplier=User.objects.create_user('import-supplier',password='x')
        self.omea=User.objects.create_user('import-omea',password='x')
        self.outsider=User.objects.create_user('import-outsider',password='x')
        Profile.objects.create(user=self.supplier,role='ADMIN_FOURNISSEUR',subsidiary=self.sub)
        Profile.objects.create(user=self.omea,role='ADMIN_OMEA',subsidiary=self.sub)

    def workbook_file(self, rows):
        workbook=Workbook(); sheet=workbook.active; sheet.title='Experts'
        sheet.append(['ORBIT']); sheet.append(['Instructions']); sheet.append([]); sheet.append(IMPORT_HEADERS)
        for row in rows: sheet.append(row)
        content=BytesIO(); workbook.save(content)
        return SimpleUploadedFile('experts.xlsx',content.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def valid_row(self, employee_id='IMP-001', code='IMP'):
        return [employee_id,'Aïcha','Diallo','Architecte Cloud',code,'Cloud','Azure, Kubernetes','Azure Architect','Télécoms','Français:C1, Anglais:B2',650,'EUR','AVAILABLE',date(2026,10,1),'Bio de test','APPROVED']

    def test_supplier_imports_own_expert_as_draft_with_references(self):
        self.client.force_login(self.supplier)
        response=self.client.post(reverse('expert_import'),{'file':self.workbook_file([self.valid_row()])})
        self.assertEqual(response.status_code,200)
        expert=Expert.objects.get(employee_id='IMP-001')
        self.assertEqual(expert.subsidiary,self.sub)
        self.assertEqual(expert.validation_status,'DRAFT')
        self.assertEqual(expert.skills.count(),2)
        self.assertEqual(expert.expertlanguageassignment_set.count(),2)
        self.assertTrue(AuditEvent.objects.filter(action='EXPERT_IMPORTED',entity_id=str(expert.pk)).exists())
        self.assertContains(response,'1 créé')

    def test_import_rejects_cross_subsidiary_and_duplicate_matricules(self):
        self.client.force_login(self.supplier)
        response=self.client.post(reverse('expert_import'),{'file':self.workbook_file([self.valid_row('MAL-001','MAL'),self.valid_row('IMP-DUP'),self.valid_row('IMP-DUP')])})
        self.assertEqual(response.status_code,200)
        self.assertFalse(Expert.objects.filter(employee_id='MAL-001').exists())
        self.assertEqual(Expert.objects.filter(employee_id='IMP-DUP').count(),1)
        self.assertContains(response,'2 erreur')

    def test_import_permission_template_and_invalid_file_are_checked(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse('expert_import')).status_code,403)
        self.client.force_login(self.omea)
        self.assertEqual(self.client.get(reverse('expert_import_template')).status_code,200)
        invalid=SimpleUploadedFile('experts.csv',b'a,b')
        response=self.client.post(reverse('expert_import'),{'file':invalid})
        self.assertContains(response,'doit être un .xlsx')
