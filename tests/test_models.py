from django.test import TestCase

from crunch.django.app import models, enums

from django.contrib.contenttypes.models import ContentType


class CrunchTestCase(TestCase):
    def setUp(self):
        ContentType.objects.clear_cache()  # needed because of this issue https://github.com/django-polymorphic/django-polymorphic/issues/470


class FilesizeAttributeTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.item = models.Item.objects.create(name="Test Item")
        self.value = 1_234_000
        self.attribute = models.FilesizeAttribute.objects.create(
            item=self.item, value=self.value
        )

    def test_value_dict(self):
        result = self.attribute.value_dict()
        assert isinstance(result, dict)
        assert "value" in result.keys()
        assert result["value"] == self.value

    def test_value_html(self):
        result = self.attribute.value_html()
        assert isinstance(result, str)
        assert result == "1.2 MB"

    def test_value_str(self):
        result = self.attribute.value_str()
        assert isinstance(result, str)
        assert result == "1.2 MB"


class LatLongAttributeTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.item = models.Item.objects.create(name="Test Item")
        self.latitude = 50
        self.longitude = 20
        self.attribute = models.LatLongAttribute.objects.create(
            item=self.item, latitude=self.latitude, longitude=self.longitude
        )

    def test_value_dict(self):
        result = self.attribute.value_dict()
        assert isinstance(result, dict)
        assert "latitude" in result.keys()
        assert "longitude" in result.keys()
        assert result["latitude"] == self.latitude
        assert result["longitude"] == self.longitude

    def test_value_html(self):
        result = self.attribute.value_html()
        assert isinstance(result, str)
        assert result == "<a href='https://www.google.com/maps/place/50,20'>+50+20/</a>"

    def test_value_str(self):
        result = self.attribute.value_str()
        assert isinstance(result, str)
        assert result == "+50+20/"


class URLAttributeTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.item = models.Item.objects.create(name="Test Item")
        self.url = "http://www.example.com"
        self.attribute = models.URLAttribute.objects.create(
            item=self.item, key="url", value=self.url
        )

    def test_value_dict(self):
        result = self.attribute.value_dict()
        assert isinstance(result, dict)
        assert result["value"] == self.url

    def test_value_html(self):
        result = self.attribute.value_html()
        assert isinstance(result, str)
        assert result == f"<a href='http://www.example.com'>http://www.example.com</a>"

    def test_value_str(self):
        result = self.attribute.value_str()
        assert isinstance(result, str)
        assert result == self.url


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


class OneEachCategory(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset1 = models.Dataset.objects.create(
            name="Test Dataset1", parent=self.project
        )
        self.dataset2 = models.Dataset.objects.create(
            name="Test Dataset2", parent=self.project
        )
        self.dataset3 = models.Dataset.objects.create(
            name="Test Dataset3", parent=self.project
        )
        self.dataset4 = models.Dataset.objects.create(
            name="Test Dataset4", parent=self.project
        )
        models.Status.objects.create(
            dataset=self.dataset2, stage=enums.Stage.SETUP, state=enums.State.START
        )
        models.Status.objects.create(
            dataset=self.dataset3, stage=enums.Stage.WORKFLOW, state=enums.State.FAIL
        )
        models.Status.objects.create(
            dataset=self.dataset4, stage=enums.Stage.UPLOAD, state=enums.State.SUCCESS
        )

    def test_unprocessed(self):
        unprocessed = models.Dataset.unprocessed()
        assert unprocessed.count() == 1
        assert self.dataset1 in unprocessed

    def test_running(self):
        running = models.Dataset.running()
        assert running.count() == 1
        assert self.dataset2 in running

    def test_failed(self):
        running = models.Dataset.failed()
        assert running.count() == 1
        assert self.dataset3 in running

    def test_completed(self):
        running = models.Dataset.completed()
        assert running.count() == 1
        assert self.dataset4 in running

    def test_next_unprocessed(self):
        next = models.Dataset.next_unprocessed()
        assert next.id == self.dataset1.id

    def test_project_unprocessed(self):
        unprocessed = self.project.unprocessed_datasets()
        assert unprocessed.count() == 1
        assert self.dataset1 in unprocessed

    def test_project_running_datasets(self):
        running = self.project.running_datasets()
        assert running.count() == 1
        assert self.dataset2 in running

    def test_project_failed_datasets(self):
        running = self.project.failed_datasets()
        assert running.count() == 1
        assert self.dataset3 in running

    def test_project_completed_datasets(self):
        running = self.project.completed_datasets()
        assert running.count() == 1
        assert self.dataset4 in running

    def test_project_next_unprocessed_dataset(self):
        next = self.project.next_unprocessed_dataset()
        assert next.id == self.dataset1.id
