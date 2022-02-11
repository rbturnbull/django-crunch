# Generated by Django 3.2.12 on 2022-02-11 00:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crunch', '0005_project_snakefile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attribute',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='charattribute',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='floatattribute',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='integerattribute',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AddField(
            model_name='attribute',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attribute',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='project',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('stage', models.IntegerField(choices=[(1, 'Setup'), (2, 'Workflow'), (3, 'Upload')])),
                ('state', models.IntegerField(choices=[(1, 'Start'), (2, 'Fail'), (3, 'Success')])),
                ('note', models.TextField(blank=True, default='')),
                ('agent_user', models.CharField(blank=True, default='', help_text='The name of the user running the agent (see https://docs.python.org/3/library/getpass.html).', max_length=255)),
                ('system', models.CharField(blank=True, default='', help_text="Returns the system/OS name, such as 'Linux', 'Darwin', 'Java', 'Windows' (see https://docs.python.org/3/library/platform.html).", max_length=255)),
                ('system_release', models.CharField(blank=True, default='', help_text="Returns the system’s release, e.g. '2.2.0' or 'NT' (see https://docs.python.org/3/library/platform.html).", max_length=255)),
                ('system_version', models.CharField(blank=True, default='', help_text="Returns the system’s release version, e.g. '#3 on degas' (see https://docs.python.org/3/library/platform.html).", max_length=255)),
                ('machine', models.CharField(blank=True, default='', help_text="Returns the machine type, e.g. 'i386' (see https://docs.python.org/3/library/platform.html).", max_length=255)),
                ('hostname', models.CharField(blank=True, default='', help_text='The hostname of the machine where the agent was running (see https://docs.python.org/3/library/socket.html).', max_length=255)),
                ('ip_address', models.CharField(blank=True, default='', help_text='The hostname in IPv4 address format (see https://docs.python.org/3/library/socket.html).', max_length=255)),
                ('mac_address', models.CharField(blank=True, default='', help_text='The hardware address  (see https://docs.python.org/3/library/uuid.html).', max_length=255)),
                ('memory_total', models.PositiveIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True)),
                ('memory_free', models.PositiveIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True)),
                ('disk_total', models.PositiveIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True)),
                ('disk_free', models.PositiveIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statuses', to='crunch.dataset')),
                ('site_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
