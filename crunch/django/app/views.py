from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from rest_framework import viewsets
from rest_framework import permissions
from . import models, serializers


class ProjectListView(PermissionRequiredMixin, ListView):
    model = models.Project
    paginate_by = 50
    permission_required = "crunch.view_project"


class ProjectDetailView(PermissionRequiredMixin, DetailView):
    model = models.Project
    permission_required = "crunch.view_project"
    # lookup_field = 'slug'


class ProjectAPI(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    # permission_classes = [permissions.DjangoModelPermissions]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class DatasetAPI(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    lookup_field = 'slug'


