from django.test import TestCase

from crunch.django.app import models, enums

from django.contrib.contenttypes.models import ContentType


class CrunchTestCase(TestCase):
    def setUp(self):
        ContentType.objects.clear_cache()  # needed because of this issue https://github.com/django-polymorphic/django-polymorphic/issues/470


class ProjectTests(CrunchTestCase):
    def test_slug(self):
        project = models.Project(name="Test Project")
        project.save()
        self.assertEqual(project.slug, "test-project")

    def test_slug2(self):
        project = models.Project.objects.create(name="Test Project 2")
        self.assertEqual(project.slug, "test-project-2")


class DatasetTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(
            name="Test Dataset", parent=self.project
        )

    def test_slug(self):
        self.assertEqual(self.dataset.slug, "test-project:test-dataset")


class StatusTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(
            name="Test Dataset", parent=self.project
        )

    def test_dataset_locking(self):
        assert not self.dataset.locked
        status = models.Status.objects.create(
            dataset=self.dataset, stage=enums.Stage.SETUP, state=enums.State.START
        )
        assert self.dataset.locked


class OneDatasetStarted(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(
            name="Test Dataset", parent=self.project
        )
        self.dataset2 = models.Dataset.objects.create(
            name="Test Dataset2", parent=self.project
        )
        self.dataset3 = models.Dataset.objects.create(
            name="Test Dataset3", parent=self.project
        )
        models.Status.objects.create(
            dataset=self.dataset2, stage=enums.Stage.SETUP, state=enums.State.START
        )

    def test_unprocessed(self):
        unprocessed = models.Dataset.unprocessed()
        assert unprocessed.count() == 2
        assert self.dataset2 not in unprocessed
        assert self.dataset3 in unprocessed
        assert self.dataset in unprocessed

    def test_running(self):
        running = models.Dataset.running()
        assert running.count() == 1
        assert self.dataset2 in running

    def test_failed(self):
        assert models.Dataset.failed().count() == 0

    def test_completed(self):
        assert models.Dataset.completed().count() == 0

    def test_has_status(self):
        has_status = models.Dataset.has_status()
        assert has_status.count() == 1
        assert self.dataset2 in has_status
