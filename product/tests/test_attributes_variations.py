"""
Tests for attributes and its variations APIs.
"""
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from product.models import Attribute, Category, Product

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

        create_attribute(self.user, name='color')
        create_attribute(self.user, name='size')
        create_attribute(self.user, name='resolution')

        r = self.client.get(ATTRIBUTES_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 3)

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

    def test_filter_attributes_by_category(self):
        """Test retrieving list of attributes and filtering it by category."""

        category = Category.objects.create(user=self.user, name='Bags')

        a1 = create_attribute(self.user)
        a2 = create_attribute(self.user)
        create_attribute(self.user)

        a1.categories.add(category)
        a2.categories.add(category)

        params = {'category': category.id}

        r = self.client.get(ATTRIBUTES_URL, params)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)

    def test_filter_attributes_by_product(self):
        """Test retrieving list of attributes and filtering it by product."""

        product = Product.objects.create(
            user=self.user,
            name='Sample product name',
            description='Sample product description.'
        )

        a1 = create_attribute(self.user)
        create_attribute(self.user)
        create_attribute(self.user)

        product.attributes.add(a1)

        params = {'product_slug': product.slug}

        r = self.client.get(ATTRIBUTES_URL, params)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_create_attribute_assigned_to_category(self):
        """Test creating an attribute assigned to a category."""

        category = Category.objects.create(user=self.user, name='Bags')

        payload = {
            'name': 'Color',
            'description': 'Sample description',
            'categories': [
                {
                    'id': category.id,
                    'name': 'bags'
                }
            ]
        }

        r = self.client.post(ATTRIBUTES_URL, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(r.data['categories']), 1)
        cat1 = r.data['categories'][0]
        self.assertEqual(cat1['name'], category.name)

    def test_update_attribute_assign_category(self):
        """Test updating an attribute and assigning a category."""

        category = Category.objects.create(user=self.user, name='Shoes')

        attribute = create_attribute(self.user, name='color')

        payload = {
            'description': 'Another description',
            'categories': [
                {
                    'id': category.id,
                    'name': category.name
                }
            ]
        }

        attribute.refresh_from_db()

        url = get_attr_detail_url(attribute.id)
        r = self.client.patch(url, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data['categories']), 1)
        cat1 = r.data['categories'][0]
        self.assertEqual(cat1['name'], category.name)