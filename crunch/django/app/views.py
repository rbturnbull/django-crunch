from django.http import HttpResponse
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
    API endpoint that allows projects to be viewed or edited.
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
    API endpoint that allows datasets to be viewed or edited.
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


class ProjectNextDatasetReference(APIView):
    """
    Retuns the study accession ID and the batch index to process next for a particular project.
    """
    permission_classes = [permissions.IsAuthenticated] # should be 'view_dataset'
        
    def get(self, request, format=None, slug=None):
        assert slug is not None
        project = models.Project.objects.get(slug=slug)
        dataset = project.next_unprocessed_dataset()

        dataset_reference = dict(project=dataset.parent.slug, dataset=dataset.slug) if dataset else dict(project="", dataset="")
        serializer = serializers.DatasetReferenceSerializer(dataset_reference)
        return Response(serializer.data)


class NextDatasetReference(APIView):
    """
    Retuns the study accession ID and the batch index to process next.
    """
    permission_classes = [permissions.IsAuthenticated] # should be 'view_dataset'
        
    def get(self, request, format=None):
        dataset = models.Dataset.next_unprocessed()

        dataset_reference = dict(project=dataset.parent.slug, dataset=dataset.slug) if dataset else dict(project="", dataset="")
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
##  Item Views
######################################################

class ItemDetailView(PermissionRequiredMixin, DetailView):
    model = models.Item
    permission_required = "crunch.view_item"
    lookup_field = 'slug'


class ItemCreateView(PermissionRequiredMixin, CreateView):
    model = models.Item
    permission_required = "crunch.add_item"


class ItemUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Item
    template_name = "crunch/form.html"
    # form_class = ItemForm
    permission_required = "crunch.update_item"
    extra_context = dict(
        form_title="Update Item",
    )


class ItemMapView(ItemDetailView):
    def get(self, request, slug) -> HttpResponse:
        item = self.get_object()
        map = item.map()
        html = map.to_html(as_string=True) if map else "<p>No map available</p>"
        return HttpResponse(html)


class ItemAPI(viewsets.ModelViewSet):
    """
    API endpoint that allows items to be viewed or edited.
    """
    queryset = models.Item.objects.all()
    serializer_class = serializers.ItemSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    lookup_field = 'slug'


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


class FilesizeAttributeAPI(viewsets.ModelViewSet):
    queryset = models.FilesizeAttribute.objects.all()
    serializer_class = serializers.FilesizeAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class BooleanAttributeAPI(viewsets.ModelViewSet):
    queryset = models.BooleanAttribute.objects.all()
    serializer_class = serializers.BooleanAttributeSerializer
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


class DateAttributeAPI(viewsets.ModelViewSet):
    queryset = models.DateAttribute.objects.all()
    serializer_class = serializers.DateAttributeSerializer
    permission_classes = [permissions.DjangoModelPermissions]
