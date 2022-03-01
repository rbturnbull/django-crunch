from django.urls import include, path
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectAPI)
router.register(r'datasets', views.DatasetAPI)
router.register(r'attributes/chars', views.CharAttributeAPI)
router.register(r'attributes/floats', views.FloatAttributeAPI)
router.register(r'attributes/integers', views.IntegerAttributeAPI)
router.register(r'attributes/urls', views.URLAttributeAPI)

# router.register(r'statuses', views.St)

#     path('api/status/', apiviews.BatchStatusListCreateAPIView.as_view(), name='api.status_list'),

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
    
    path("datasets/create/", views.DatasetCreateView.as_view(), name="dataset-create"),
    path('projects/<str:project>/datasets/', RedirectView.as_view(url="..", permanent=False)),
    path('projects/<str:project>/datasets/<str:slug>', views.DatasetDetailView.as_view(), name='dataset-detail'),
    path("projects/<str:project>/datasets/<str:slug>/update/", views.DatasetUpdateView.as_view(), name="dataset-update"),

]