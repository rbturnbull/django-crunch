from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter

from . import models

class ProjectChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = models.Project  # Optional, explicitly set here.


# @admin.register(models.Project)
# class ProjectParentAdmin(PolymorphicParentModelAdmin):
#     """ The parent model admin """
#     base_model = models.Project  # Optional, explicitly set here.
#     list_filter = (PolymorphicChildModelFilter,)  # This is optional.


class AttributeChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Attribute


@admin.register(models.CharAttribute)
class CharAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.IntegerAttribute)
class IntegerAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.FilesizeAttribute)
class FilesizeAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.FloatAttribute)
class FloatAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.URLAttribute)
class URLAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.LatLongAttribute)
class LatLongAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.DateTimeAttribute)
class DateTimeAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.DateAttribute)
class DateAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.BooleanAttribute)
class BooleanAttributeAdmin(AttributeChildAdmin):
    pass


@admin.register(models.Attribute)
class AttributeParentAdmin(PolymorphicParentModelAdmin):
    base_model = models.Attribute  # Optional, explicitly set here.
    child_models = (
        models.IntegerAttribute, 
        models.FilesizeAttribute, 
        models.FloatAttribute, 
        models.CharAttribute,
        models.URLAttribute,
        models.BooleanAttribute,
        models.DateAttribute,
        models.DateTimeAttribute,
    ) # This should be automatic
    list_filter = (PolymorphicChildModelFilter,)  # This is optional.


admin.site.register(models.Project)
admin.site.register(models.Dataset)
admin.site.register(models.Item)
admin.site.register(models.Status)
# admin.site.register(models.Attribute)


