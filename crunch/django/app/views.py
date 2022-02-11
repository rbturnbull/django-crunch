from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
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
    permission_classes = [permissions.DjangoModelPermissions]
    lookup_field = 'slug'


class DatasetDetailView(PermissionRequiredMixin, DetailView):
    model = models.Dataset
    permission_required = "crunch.view_dataset"
    lookup_field = 'slug'


class DatasetAPI(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    lookup_field = 'slug'


class NextDatasetReference(APIView):
    """
    Retuns the study accession ID and the batch index to process next.
    """
    permission_classes = [permissions.IsAuthenticated] # should be 'view_dataset'
        
    def get(self, request, format=None):
        dataset = models.Dataset.next_unprocessed()

        dataset_reference = dict(project=dataset.project.slug, dataset=dataset.slug) if dataset else dict(project="", dataset="")
        serializer = serializers.DatasetReferenceSerializer(dataset_reference)
        return Response(serializer.data)


class StatusListCreateAPIView(generics.ListCreateAPIView):
    queryset = models.Status.objects.all()
    serializer_class = serializers.StatusSerializer

    def perform_create(self, serializer):
        serializer.save(
            site_user=self.request.user,
        )
