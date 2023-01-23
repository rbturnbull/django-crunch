# Generated by Django 3.2.12 on 2022-04-04 00:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crunch', '0005_alter_item_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilesizeAttribute',
            fields=[
                ('attribute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crunch.attribute')),
                ('value', models.PositiveBigIntegerField(help_text='The filesize of this item in bytes.')),
            ],
            options={
                'abstract': False,
            },
            bases=('crunch.attribute',),
        ),
    ]