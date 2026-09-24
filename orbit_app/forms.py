from django import forms
from .models import Expert, ExpertRequest, Evaluation, Subsidiary
from .selectors import role, subsidiary_id

LABELS = {
 'first_name':'Prénom','last_name':'Nom','employee_id':'Matricule','job_title':'Fonction',
 'subsidiary':'Filiale','domains':'Domaines d’expertise','skills':'Compétences','certifications':'Certifications',
 'verticals':'Verticales métier','daily_rate':'TJM','currency':'Devise','availability':'Disponibilité',
 'bio':'Présentation','available_from':'Disponible à partir du','title':'Titre de la demande','description':'Contexte et besoin',
 'domain':'Domaine d’expertise','required_skills':'Compétences recherchées','required_language':'Langue requise',
 'min_language_level':'Niveau linguistique minimum','max_daily_rate':'TJM maximum','desired_start':'Date de démarrage souhaitée',
 'duration_days':'Durée en jours','rating':'Note sur 5','comment':'Commentaire',
 'mode':'Mode de recherche','target_expert':'Expert à solliciter directement',
}
class StyledForm(forms.ModelForm):
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        for name,field in self.fields.items():
            field.label=LABELS.get(name,field.label)
            field.widget.attrs['class']='input'
            if isinstance(field,forms.DateField): field.widget=forms.DateInput(attrs={'type':'date','class':'input'})
            if isinstance(field.widget,forms.Textarea): field.widget.attrs['rows']=5
            if isinstance(field.widget,forms.SelectMultiple): field.help_text='Maintenez Ctrl ou Cmd pour sélectionner plusieurs valeurs.'
        if user and 'subsidiary' in self.fields and role(user) != 'ADMIN_OMEA':
            self.fields['subsidiary'].queryset=Subsidiary.objects.filter(pk=subsidiary_id(user))
            self.initial.setdefault('subsidiary',subsidiary_id(user))
class ExpertForm(StyledForm):
    class Meta:
        model=Expert
        fields=['first_name','last_name','employee_id','job_title','subsidiary','domains','skills','certifications','verticals','daily_rate','currency','availability','bio','available_from']
class ExpertRequestForm(StyledForm):
    class Meta:
        model=ExpertRequest
        fields=['mode','target_expert','title','description','subsidiary','domain','required_skills','required_language','min_language_level','max_daily_rate','desired_start','duration_days']
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,user=user,**kwargs)
        self.fields['mode'].widget=forms.RadioSelect()
        self.fields['mode'].required=False
        self.fields['mode'].initial=self.instance.mode if self.instance.pk else 'BROADCAST'
        self.fields['mode'].help_text='Diffusez votre besoin ou ciblez directement un expert du référentiel.'
        self.fields['target_expert'].queryset=Expert.objects.filter(is_active=True,validation_status='APPROVED',availability='AVAILABLE').select_related('subsidiary').order_by('last_name','first_name')
        self.fields['target_expert'].required=False
        self.fields['target_expert'].help_text='Requis uniquement pour une sollicitation directe.'
    def clean(self):
        cleaned=super().clean()
        mode=cleaned.get('mode') or 'BROADCAST'
        cleaned['mode']=mode
        if mode=='DIRECT' and not cleaned.get('target_expert'):
            self.add_error('target_expert','Choisissez l’expert à solliciter directement.')
        if mode=='BROADCAST': cleaned['target_expert']=None
        return cleaned
class EvaluationForm(StyledForm):
    class Meta: model=Evaluation; fields=['rating','comment']
