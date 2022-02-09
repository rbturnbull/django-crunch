from django.views.generic.list import ListView

from . import models

class ProjectListView(ListView):
    model = models.Project
    paginate_by = 100  # if pagination is desired

