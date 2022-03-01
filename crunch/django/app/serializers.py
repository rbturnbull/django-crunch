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
        return instance.value_dict()


class CharAttributeSerializer(serializers.ModelSerializer):
    dataset = serializers.SlugRelatedField(slug_field='slug', queryset=models.Dataset.objects.all())

    class Meta:
        model = models.CharAttribute
        fields = [
            "dataset",
            "key",
            "value",
        ]


class FloatAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FloatAttribute
        fields = [
            "dataset",
            "key",
            "value",
        ]


class IntegerAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IntegerAttribute
        fields = [
            "dataset",
            "key",
            "value",
        ]


class URLAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.URLAttribute
        fields = [
            "dataset",
            "key",
            "value",
        ]


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    # project = serializers.HyperlinkedRelatedField(view_name='crunch:api:project-detail', lookup_field='slug', queryset=models.Project.objects.all())
    project = serializers.SlugRelatedField(slug_field='slug', queryset=models.Project.objects.all())
    attributes = AttributeSerializer(many=True, required=False)

    class Meta:
        model = models.Dataset
        fields = ['id', 'name', 'slug','project', 'description', 'details', 'attributes']


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
            "version",
            "revision",
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

