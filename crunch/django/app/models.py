from operator import mod
from django.db import models
from django_extensions.db.fields import AutoSlugField


class ProjectBase(models.Model):
    name = models.CharField(max_length=1023, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Project(ProjectBase):
    pass


class DatasetBase(models.Model):
    name = models.CharField(max_length=1023, unique=True)
    slug = AutoSlugField(populate_from='name')
    project = models.ForeignKey(ProjectBase, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        unique_together = ('project', 'name',)


class Dataset(DatasetBase):
    pass





