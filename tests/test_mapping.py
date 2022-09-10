from crunch.django.app import models, enums, mapping
from .test_models import CrunchTestCase


class MappingTests(CrunchTestCase):
    def setUp(self):
        super().setUp()
        self.item = models.Item.objects.create(name="Test Item")
        self.latitude = 50
        self.longitude = 20
        self.attribute = models.LatLongAttribute.objects.create(
            item=self.item, latitude=self.latitude, longitude=self.longitude
        )

    def test_map(self):
        map = mapping.item_map(self.item)
        assert map is not None
        html = map.to_html(as_string=True)
        assert (
            '"Test Item", "latitude": 50.0, "longitude": 20.0, "url": "/items/test-item/"'
            in html
        )
