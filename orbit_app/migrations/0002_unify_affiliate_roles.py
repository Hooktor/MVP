from django.db import migrations, models


def unify_legacy_roles(apps, schema_editor):
    Profile=apps.get_model('orbit_app','Profile')
    Profile.objects.filter(role__in=['DEMANDEUR','ADMIN_DEMANDEUR','ADMIN_FOURNISSEUR']).update(role='ADMIN_FILIALE')


class Migration(migrations.Migration):
    dependencies=[('orbit_app','0001_initial')]
    operations=[
        migrations.AlterField(
            model_name='profile', name='role',
            field=models.CharField(choices=[('ADMIN_FILIALE','Administrateur de filiale'),('ADMIN_OMEA','Administrateur OMEA')],default='ADMIN_FILIALE',max_length=30),
        ),
        migrations.RunPython(unify_legacy_roles,migrations.RunPython.noop),
    ]
