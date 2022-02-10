from rest_framework import serializers

from . import models

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ['name', 'slug',]


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(view_name='crunch:api:project-detail', read_only='True', lookup_field='slug')

    class Meta:
        model = models.Dataset
        fields = ['name', 'slug','project']
