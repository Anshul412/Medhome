import uuid

from django.db import migrations, models


def populate_ice_tokens(apps, schema_editor):
    PatientProfile = apps.get_model('accounts', 'PatientProfile')
    for profile in PatientProfile.objects.filter(ice_token__isnull=True).iterator():
        profile.ice_token = uuid.uuid4()
        profile.save(update_fields=('ice_token',))


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientprofile',
            name='ice_token',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(
            populate_ice_tokens,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='patientprofile',
            name='ice_token',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
