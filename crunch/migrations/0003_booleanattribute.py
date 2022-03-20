# Generated by Django 3.2.12 on 2022-03-20 06:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crunch', '0002_auto_20220320_0535'),
    ]

    operations = [
        migrations.CreateModel(
            name='BooleanAttribute',
            fields=[
                ('attribute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crunch.attribute')),
                ('value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('crunch.attribute',),
        ),
    ]
