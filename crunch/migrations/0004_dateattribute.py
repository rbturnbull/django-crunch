# Generated by Django 3.2.12 on 2022-03-20 07:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crunch', '0003_booleanattribute'),
    ]

    operations = [
        migrations.CreateModel(
            name='DateAttribute',
            fields=[
                ('attribute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crunch.attribute')),
                ('value', models.DateField()),
            ],
            options={
                'abstract': False,
            },
            bases=('crunch.attribute',),
        ),
    ]