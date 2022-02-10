from django.urls import include, path
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from rest_framework import routers


from . import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectAPI)
router.register(r'datasets', views.DatasetAPI)


app_name = "crunch"
urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('api/', include( (router.urls, 'api') )),
    path('projects/', RedirectView.as_view(url="..", permanent=False)),
    path('projects/<str:slug>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<str:project>/datasets/', RedirectView.as_view(url="..", permanent=False)),
    path('projects/<str:project>/datasets/<str:slug>', views.DatasetDetailView.as_view(), name='dataset-detail'),
]