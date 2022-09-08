from django.urls import reverse
from rest_framework import status as drf_status
from rest_framework.test import APITestCase
from crunch.django.app.models import Status
from django.contrib.auth import get_user_model
from crunch.django.app import models, enums


class StatusTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.username = "username"
        self.password = "password-for-unit-testing"
        self.user = User.objects.create_superuser(username=self.username, password=self.password)
        self.project = models.Project.objects.create(name="Test Project")
        self.dataset = models.Dataset.objects.create(name="Test Dataset", parent=self.project)


    def test_create_status(self):
        """
        Ensure we can create a new status.
        """
        url = reverse('crunch:status-list')
        data = {'dataset': self.dataset.id, 'stage': enums.Stage.SETUP, 'state': enums.State.SUCCESS, 'note': ''}
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)
        self.assertEqual(Status.objects.count(), 1)
        status = Status.objects.get()
        self.assertEqual(status.dataset.id, self.dataset.id)
        self.assertEqual(status.stage, enums.Stage.SETUP)
        self.assertEqual(status.state, enums.State.SUCCESS)
