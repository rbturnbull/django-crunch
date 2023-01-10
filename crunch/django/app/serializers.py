from rest_framework import serializers

from . import models

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'slug', 'description', 'details', 'workflow']


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attribute
        fields = ['id', 'key', ]

    def to_representation(self, instance):
        return instance.value_dict()


class AbstractAttributeSerializer(serializers.ModelSerializer):
    item = serializers.SlugRelatedField(slug_field='slug', queryset=models.Item.objects.all())
    class Meta:
        fields = [
            "item",
            "key",
            "value",
        ]


class CharAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.CharAttribute


class FloatAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.FloatAttribute


class IntegerAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.IntegerAttribute


class FilesizeAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.FilesizeAttribute


class BooleanAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.BooleanAttribute


class URLAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.URLAttribute


class DateTimeAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.DateTimeAttribute


class DateAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.DateAttribute


class LatLongAttributeSerializer(AbstractAttributeSerializer):
    class Meta(AbstractAttributeSerializer.Meta):
        model = models.LatLongAttribute
        fields = [
            "item",
            "key",
            "latitude",
            "longitude",
        ]


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.SlugRelatedField(slug_field='slug', queryset=models.Item.objects.all())
    attributes = AttributeSerializer(many=True, required=False)

    class Meta:
        model = models.Item
        fields = ['id', 'name', 'slug','parent', 'description', 'details', 'attributes']


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.SlugRelatedField(slug_field='slug', queryset=models.Project.objects.all())
    attributes = AttributeSerializer(many=True, required=False)
    items = ItemSerializer(many=True, required=False)

    class Meta:
        model = models.Dataset
        fields = ['id', 'name', 'slug','parent', 'description', 'details', 'attributes', 'items', 'base_file_path']


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

