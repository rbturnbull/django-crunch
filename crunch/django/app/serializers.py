from rest_framework import serializers

from . import models

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ['name', 'slug',]


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attribute
        fields = ['key', ]

    def to_representation(self, instance):
        return instance.as_dict()


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(view_name='crunch:api:project-detail', read_only='True', lookup_field='slug')
    attribute_set = AttributeSerializer(many=True)

    class Meta:
        model = models.Dataset
        fields = ['name', 'slug','project', 'attribute_set']
