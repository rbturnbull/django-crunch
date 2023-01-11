from django.urls import include, path
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectAPI)
router.register(r'datasets', views.DatasetAPI)
router.register(r'items', views.ItemAPI)
router.register(r'attributes/char', views.CharAttributeAPI)
router.register(r'attributes/float', views.FloatAttributeAPI)
router.register(r'attributes/int', views.IntegerAttributeAPI)
router.register(r'attributes/filesize', views.FilesizeAttributeAPI)
router.register(r'attributes/bool', views.BooleanAttributeAPI)
router.register(r'attributes/url', views.URLAttributeAPI)
router.register(r'attributes/lat-long', views.LatLongAttributeAPI)
router.register(r'attributes/datetime', views.DateTimeAttributeAPI)
router.register(r'attributes/date', views.DateAttributeAPI)

app_name = "crunch"
urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('api/', include( (router.urls, 'api') )),
    path('api/statuses/', views.StatusListCreateAPIView.as_view(), name='status-list'),
    path('api/next/', views.NextDatasetReference.as_view(), name='next'),

    path('projects/', RedirectView.as_view(url="..", permanent=False)),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
    path('projects/<str:slug>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path("projects/<str:slug>/update/", views.ProjectUpdateView.as_view(), name="project-update"),
    path("api/projects/<str:slug>/next/", views.ProjectNextDatasetReference.as_view(), name="project-api-next"),
    
    path("datasets/create/", views.DatasetCreateView.as_view(), name="dataset-create"),
    path('projects/<str:project>/datasets/', RedirectView.as_view(url="..", permanent=False)),
    path('projects/<str:project>/datasets/<str:slug>', views.DatasetDetailView.as_view(), name='dataset-detail'),
    path("projects/<str:project>/datasets/<str:slug>/update/", views.DatasetUpdateView.as_view(), name="dataset-update"),

    path("items/create/", views.ItemCreateView.as_view(), name="item-create"),
    path('items/<str:slug>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('items/<str:slug>/map/', views.ItemMapView.as_view(), name='item-map'),
    path('items/<str:slug>/update/', views.ItemUpdateView.as_view(), name='item-update'),
]