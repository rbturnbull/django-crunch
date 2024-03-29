# Generated by Django 3.2.15 on 2022-09-08 00:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crunch', '0009_auto_20220811_0231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='disk_free',
            field=models.BigIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='disk_total',
            field=models.BigIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='memory_free',
            field=models.BigIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='memory_total',
            field=models.BigIntegerField(blank=True, default=None, help_text='See https://psutil.readthedocs.io/en/latest/', null=True),
        ),
    ]
