from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin

from . import models

class ProjectListView(PermissionRequiredMixin, ListView):
    model = models.Project
    paginate_by = 50
    permission_required = "crunch.view_project"


class ProjectDetailView(PermissionRequiredMixin, DetailView):
    model = models.Project
    permission_required = "crunch.view_project"


