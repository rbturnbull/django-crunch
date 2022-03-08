from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from . import models, serializers


######################################################
##  Project Views
######################################################

class ProjectListView(PermissionRequiredMixin, ListView):
    model = models.Project
    paginate_by = 50
    permission_required = "crunch.view_project"


class ProjectDetailView(PermissionRequiredMixin, DetailView):
    model = models.Project
    permission_required = "crunch.view_project"
    # lookup_field = 'slug'


class ProjectCreateView(PermissionRequiredMixin, CreateView):
    model = models.Project
    permission_required = "crunch.add_project"


class ProjectUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Project
    template_name = "crunch/form.html"
    # form_class = ProjectForm
    permission_required = "crunch.update_project"
    extra_context = dict(
        form_title="Update Project",
    )


class ProjectAPI(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    lookup_field = 'slug'


######################################################
##  Dataset Views
######################################################


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


class DatasetCreateView(PermissionRequiredMixin, CreateView):
    model = models.Dataset
    permission_required = "crunch.add_dataset"


class DatasetUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Dataset
    template_name = "crunch/form.html"
    # form_class = DatasetForm
    permission_required = "crunch.update_dataset"
    extra_context = dict(
        form_title="Update Dataset",
    )


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


######################################################
##  Attribute Views
######################################################

class CharAttributeAPI(viewsets.ModelViewSet):
    queryset = models.CharAttribute.objects.all()
    serializer_class = serializers.CharAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class FloatAttributeAPI(viewsets.ModelViewSet):
    queryset = models.FloatAttribute.objects.all()
    serializer_class = serializers.FloatAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class IntegerAttributeAPI(viewsets.ModelViewSet):
    queryset = models.IntegerAttribute.objects.all()
    serializer_class = serializers.IntegerAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class FloatAttributeAPI(viewsets.ModelViewSet):
    queryset = models.FloatAttribute.objects.all()
    serializer_class = serializers.FloatAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class URLAttributeAPI(viewsets.ModelViewSet):
    queryset = models.URLAttribute.objects.all()
    serializer_class = serializers.URLAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class LatLongAttributeAPI(viewsets.ModelViewSet):
    queryset = models.LatLongAttribute.objects.all()
    serializer_class = serializers.LatLongAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class DateTimeAttributeAPI(viewsets.ModelViewSet):
    queryset = models.DateTimeAttribute.objects.all()
    serializer_class = serializers.DateTimeAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]
