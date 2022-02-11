from rest_framework import serializers

from . import models

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'slug','snakefile']


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attribute
        fields = ['id', 'key', ]

    def to_representation(self, instance):
        return instance.as_dict()


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(view_name='crunch:api:project-detail', read_only='True', lookup_field='slug')
    attributes = AttributeSerializer(many=True)

    class Meta:
        model = models.Dataset
        fields = ['id', 'name', 'slug','project', 'attributes']


class DatasetReferenceSerializer(serializers.Serializer):
    project = serializers.CharField(max_length=255)
    dataset = serializers.CharField(max_length=255)

    

class StatusSerializer(serializers.ModelSerializer):
    dataset = serializers.PrimaryKeyRelatedField(queryset=models.Dataset.objects.all())

    class Meta:
        model = models.Status
        fields = [
            "id", 
            "dataset", 
            "site_user", 
            "stage", 
            "state", 
            "note",
            "agent_user",
            "system",
            "system_release",
            "system_version",
            "machine",
            "hostname",
            "ip_address",
            "mac_address",
            "memory_total",
            "memory_free",
            "disk_total",
            "disk_free",
        ]

