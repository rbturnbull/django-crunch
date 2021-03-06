from django.test import TestCase

from crunch.django.app import models

from django.contrib.contenttypes.models import ContentType


class CrunchTestCase(TestCase):
    def setUp(self):
        ContentType.objects.clear_cache() # needed because of this issue https://github.com/django-polymorphic/django-polymorphic/issues/470


class ProjectTests(CrunchTestCase):
    def test_slug(self):
        project = models.Project(name="Test Project")
        project.save()
        self.assertEqual(project.slug, "test-project")

    def test_slug2(self):
        project = models.Project.objects.create(name="Test Project 2")
        self.assertEqual(project.slug, "test-project-2")


class DatasetTests(CrunchTestCase):
    def test_slug(self):
        project = models.Project.objects.create(name="Test Project")
        dataset = models.Dataset.objects.create(name="Test Dataset", parent=project)

        self.assertEqual(dataset.slug, "test-project.test-dataset")
