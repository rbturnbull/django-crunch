from django.urls import path

from . import views

app_name = "crunch"
urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('<str:slug>/', views.ProjectDetailView.as_view(), name='project-detail'),
]