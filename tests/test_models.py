import pytest 
from unittest.mock import patch
from django.test import TestCase

from crunch.django.app import models, enums
from crunch.django.app import storages
from django.core.files.storage import FileSystemStorage

from django.contrib.contenttypes.models import ContentType


from .test_storages import MockSettings, TEST_DIR

class CrunchTestCase(TestCase):
    def setUp(self):
        super().setUp()
        ContentType.objects.clear_cache()  # needed because of this issue https://github.com/django-polymorphic/django-polymorphic/issues/470


class FilesizeAttributeTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.item = models.Item.objects.create(name="Test Item")
        self.value = 1_234_000
        self.attribute = models.FilesizeAttribute.objects.create(
            item=self.item, value=self.value, key="key",
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

    def test_type_str(self):
        assert self.attribute.type_str() == "Filesize"

    def test_str(self):
        assert str(self.attribute) == f"key: 1.2 MB"


class AttributeTestCase(CrunchTestCase):
    def test_value_str(self):
        item = models.Item.objects.create(name="Test Item")
        attribute = models.Attribute(key="item attribute", item=item)
        with pytest.raises(NotImplementedError):
            attribute.value_str()


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

    def test_type_str(self):
        assert self.attribute.type_str() == "Lat Long"


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

    def test_absolute_url(self):
        project = models.Project.objects.create(name="Test Project")
        url = project.get_absolute_url()
        assert url == "/projects/test-project/"

    def test_get_admin_url(self):
        project = models.Project.objects.create(name="Test Project")
        assert project.get_admin_url() == "/admin/crunch/project/1/change/"
    

class DatasetTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(
            name="Test Dataset", parent=self.project
        )

    def test_slug(self):
        self.assertEqual(self.dataset.slug, "test-project:test-dataset")

    def test_absolute_url(self):
        assert self.dataset.get_absolute_url() == "/projects/test-project/datasets/test-project:test-dataset"

    def test_get_admin_url(self):
        assert self.dataset.get_admin_url() == "/admin/crunch/dataset/2/change/"
    
    def test_map(self):
        latitude = 50
        longitude = 20
        assert self.dataset.has_descendant_latlongattributes() == False
        assert self.project.has_descendant_latlongattributes() == False
        models.LatLongAttribute.objects.create(
            item=self.dataset, latitude=latitude, longitude=longitude
        )
        assert self.dataset.has_descendant_latlongattributes() == True
        assert self.project.has_descendant_latlongattributes() == True

        map = self.dataset.map()
        assert map is not None
        html = map.to_html(as_string=True)
        assert (
            '"Test Dataset", "latitude": 50.0, "longitude": 20.0, "url": "/projects/test-project/datasets/test-project:test-dataset"'
            in html
        )    

    def test_dataset_files(self):
        storage = FileSystemStorage(location=TEST_DIR.absolute(), base_url="http://www.example.com")
        with patch('crunch.django.app.storages.default_storage', storage):
            self.dataset.base_file_path = TEST_DIR
            self.dataset.save()

            root_dir = self.dataset.files()
            assert isinstance(root_dir, storages.StorageDirectory)
            files = list(root_dir.file_descendents())
            assert [x.short_str() for x in files] == ['dummy-file1.txt', 'dummy-file2.txt', 'dummy-file3.txt', 'settings.json', 'settings.toml']




class StatusTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(
            name="Test Dataset", parent=self.project
        )

    def test_dataset_locking(self):
        assert not self.dataset.locked
        models.Status.objects.create(
            dataset=self.dataset, stage=enums.Stage.SETUP, state=enums.State.START
        )
        assert self.dataset.locked

    def test_status_str(self):
        status = models.Status.objects.create(
            dataset=self.dataset, stage=enums.Stage.SETUP, state=enums.State.START
        )
        assert str(status) == "Test Dataset: Setup Start"


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


class ItemTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.root = models.Item.objects.create(name="root")
        self.child1 = models.Item.objects.create(name="child1", parent=self.root)
        self.child2 = models.Item.objects.create(name="child2", parent=self.root)
        self.child3 = models.Item.objects.create(name="child3", parent=self.root)
        self.grandchild = models.Item.objects.create(name="grandchild", parent=self.child1)

    def test_descendant_total_filesize(self):
        models.FilesizeAttribute.objects.create(item=self.root, key="filesize", value=2_000_000)
        models.FilesizeAttribute.objects.create(item=self.child1, key="filesize", value=3_000_000)
        models.FilesizeAttribute.objects.create(item=self.child2, key="filesize", value=5_000_000)
        models.FilesizeAttribute.objects.create(item=self.grandchild, key="filesize", value=500_000)

        assert self.root.descendant_total_filesize() == 10_500_000
        assert self.child1.descendant_total_filesize() == 3_500_000
        assert self.child2.descendant_total_filesize() == 5_000_000
        assert self.grandchild.descendant_total_filesize() == 500_000
        assert self.child3.descendant_total_filesize() == None

        assert self.root.descendant_total_filesize_readable() == "10.5 MB"
        assert self.child1.descendant_total_filesize_readable() == "3.5 MB"
        assert self.child2.descendant_total_filesize_readable() == "5.0 MB"
        assert self.grandchild.descendant_total_filesize_readable() == "500.0 kB"
        assert self.child3.descendant_total_filesize_readable() == "None"

    def test_reslugify_descendants(self):
        self.root.slug = "root-slug-bad"
        self.root.save()

        self.grandchild.slug = "grandchild-slug-bad"
        self.grandchild.save()

        self.root.reslugify_descendants()

        models.Item.objects.get(name="root").slug == "root"
        models.Item.objects.get(name="grandchild").slug == "grandchild"
        
    def test_next_prev(self):
        assert self.root.next_in_order() == self.child1
        assert self.root.prev_in_order() == None
        assert self.root.prev_in_order(loop=True) == self.child3

        

