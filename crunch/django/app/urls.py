from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectAPI)
router.register(r'datasets', views.DatasetAPI)


app_name = "crunch"
urlpatterns = [
    path('', views.ProjectListView.as_view(), name='home'),
    path('api/', include( (router.urls, 'api') )),
    # path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/<str:slug>/', views.ProjectDetailView.as_view(), name='proj-detail'),
]