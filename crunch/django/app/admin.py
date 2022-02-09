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


admin.site.register(models.Project)
admin.site.register(models.Dataset)


