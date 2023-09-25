"""
Tests for attributes and its variations APIs.
"""
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from product.models import Attribute, Variation
from product.serializers import AttributeSerializer

ATTRIBUTES_URL = reverse('attribute-list')


def get_attr_detail_url(attr_id):
    """Create and return the url of an attribute detail page."""

    return reverse('attribute-detail', args=[attr_id])


def create_attribute(user, **params):
    defaults = {
        'name': 'sample attribute',
        'description': 'Sample attribute description'
    }
    defaults.update(**params)

    return Attribute.objects.create(user=user, **defaults)


class AttributeTests(TestCase):
    """Tests for attribute APIs."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test_attr_user@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_list_attributes(self):
        """Tests retrieving all the attributes of the user."""

        a1 = create_attribute(self.user, name='color')
        a2 = create_attribute(self.user, name='size')
        a3 = create_attribute(self.user, name='resolution')

        srs = AttributeSerializer((a1, a2, a3), many=True)

        r = self.client.get(ATTRIBUTES_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 3)
        self.assertEqual(r.data, srs)

    def test_create_attribute(self):
        """Test creating an attribute."""

        payload = {
            'name': 'Color',
            'description': 'Sample description'
        }

        r = self.client.post(ATTRIBUTES_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['name'], payload['name'].lower())
        self.assertEqual(r.data['description'], payload['description'])

    def test_update_attribute(self):
        """Test updating an attribute."""

        attribute = create_attribute(self.user)
        payload = {'name': 'Color'}
        url = get_attr_detail_url(attribute.id)

        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        attribute.refresh_from_db()
        self.assertEqual(attribute.name, payload['name'].lower())

    def test_remove_attribute(self):
        """Test removing an attribute."""

        attribute = create_attribute(self.user)
        url = get_attr_detail_url(attribute.id)

        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
