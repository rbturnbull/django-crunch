from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.urls import reverse

from polymorphic.models import PolymorphicModel

class Project(PolymorphicModel):
    name = models.CharField(max_length=1023, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("crunch:project-detail", kwargs={"slug": self.slug})
    

class Dataset(PolymorphicModel):
    name = models.CharField(max_length=1023)
    slug = AutoSlugField(populate_from='name')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('project', 'name',)

    def get_absolute_url(self):
        return f"{self.project.get_absolute_url()}datasets/{self.slug}"


class Attribute(PolymorphicModel):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=1023)
    






