from django.urls import reverse
from rest_framework import status as drf_status
from rest_framework.test import APITestCase
from crunch.django.app.models import Status
from django.contrib.auth import get_user_model
from crunch.django.app import models, enums

from .test_models import CrunchTestCase

class ViewsTests(CrunchTestCase, APITestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.username = "username"
        self.password = "password-for-unit-testing"
        self.user = User.objects.create_superuser(username=self.username, password=self.password)
        self.project1 = models.Project.objects.create(name="Test Project 1")
        self.project2 = models.Project.objects.create(name="Test Project 2")
        self.dataset1 = models.Dataset.objects.create(name="Test Dataset 1", parent=self.project1, description="description1", details="details1")
        self.dataset2 = models.Dataset.objects.create(name="Test Dataset 2", parent=self.project2)

    def test_create_status(self):
        """
        Ensure we can create a new status.
        """
        url = reverse('crunch:status-list')
        data = {'dataset': self.dataset1.id, 'stage': enums.Stage.SETUP, 'state': enums.State.SUCCESS, 'note': ''}
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)
        self.assertEqual(Status.objects.count(), 1)
        status = Status.objects.get()
        self.assertEqual(status.dataset.id, self.dataset1.id)
        self.assertEqual(status.stage, enums.Stage.SETUP)
        self.assertEqual(status.state, enums.State.SUCCESS)

    def test_next_dataset_reference(self):
        """
        check if we can get the next dataset to be processed
        """
        url = reverse('crunch:next')
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        data = response.json()
        assert data == {'project': 'test-project-1', 'dataset': 'test-project-1:test-dataset-1'}

        self.dataset1.locked = True
        self.dataset1.save()

        response = self.client.get(url)
        data = response.json()
        assert data == {'project': 'test-project-2', 'dataset': 'test-project-2:test-dataset-2'}

        self.dataset2.locked = True
        self.dataset2.save()

        response = self.client.get(url)
        data = response.json()
        assert data == {'dataset': '', 'project': ''}

    def test_project_api_next(self):
        url = reverse('crunch:project-api-next', kwargs={'slug': self.project1.slug})
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        data = response.json()
        assert data == {'project': 'test-project-1', 'dataset': 'test-project-1:test-dataset-1'}

        self.dataset1.locked = True
        self.dataset1.save()

        response = self.client.get(url)
        data = response.json()
        assert data == {'dataset': '', 'project': ''}

        url = reverse('crunch:project-api-next', kwargs={'slug': self.project2.slug})
        response = self.client.get(url)
        data = response.json()
        assert data == {'project': 'test-project-2', 'dataset': 'test-project-2:test-dataset-2'}

        self.dataset2.locked = True
        self.dataset2.save()

        response = self.client.get(url)
        data = response.json()
        assert data == {'dataset': '', 'project': ''}

    def test_item_map_view(self):
        url = reverse('crunch:item-map', kwargs={'slug': self.project1.slug})
        latitude = 50
        longitude = 20
        models.LatLongAttribute.objects.create(
            item=self.dataset1, latitude=latitude, longitude=longitude
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        content = response.content.decode()
        assert '"Test Dataset 1", "latitude": 50.0, "longitude": 20.0, "url": "/projects/test-project-1/datasets/test-project-1:test-dataset-1"' in content

    def test_dataset_api_view(self):
        url = reverse('crunch:api:dataset-detail', kwargs={'slug': self.dataset1.slug})
        latitude = 50
        longitude = 20
        # add an attribute to check that it comes through
        models.LatLongAttribute.objects.create(
            item=self.dataset1, latitude=latitude, longitude=longitude
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        data = response.json()
        assert data == {
            "id":3,
            "name":"Test Dataset 1",
            "slug":"test-project-1:test-dataset-1",
            "parent":"test-project-1",
            "description":"description1",
            "details":"details1",
            "attributes":[
                {
                    "key":"",
                    "latitude":50.0,
                    "longitude":20.0
                }
            ],
            "items":[
                
            ],
            "base_file_path":"crunch/test-project-1"
            }
        
        
    def test_project_detail_view(self):
        url = reverse('crunch:project-detail', kwargs={'slug': self.project1.slug})
        latitude = 50
        longitude = 20
        # add an attribute to check that it comes through
        models.LatLongAttribute.objects.create(
            item=self.dataset1, latitude=latitude, longitude=longitude
        )

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        content = response.content.decode()
        assert "<h3>Unprocessed Datasets</h3>" in content
        assert '<iframe class="embed-responsive-item" src="/items/test-project-1/map/" allowfullscreen></iframe>' in content

        
        
        
    