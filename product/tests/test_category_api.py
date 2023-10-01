"""
Tests for Category APIs.
"""
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from product.models import Category, Attribute

CATEGORIES_URL = reverse('category-list')


def detail_url(category_id):
    """Create and return the url of detail page."""
    return reverse('category-detail', args=[category_id])


def create_category(user, **params):
    """Create a sample category for testing purposes."""

    defaults = {
        'name': 'Sample name'
    }
    defaults.update(**params)

    return Category.objects.create(user=user, **defaults)


class PublicCategoryApiTests(TestCase):
    """Tests for category APIs when the user is not authenticated."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_category_list_access_denied_unauthenticated(self):
        """Test access denied when the user is not authenticated."""

        r = self.client.get(CATEGORIES_URL)

        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCategoryApiTests(TestCase):
    """Tests for category APIs."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test_user_1@example.com',
            name='Test Name',
            password='test_123_pass'
        )
        self.client.force_authenticate(self.user)

    def test_get_category_list_success(self):
        """Test retrieving the list of categories."""
        create_category(self.user)
        create_category(self.user, name='another name')

        r = self.client.get(CATEGORIES_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)

    def test_create_category_without_parent(self):
        """Test creating a category that doesn't have any parent category."""
        payload = {
            'name': 'Detectives'
        }
        r = self.client.post(CATEGORIES_URL, payload)
        category = Category.objects.get(id=r.data['id'])

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(category.name, payload['name'].lower())

    def test_create_category_with_attributes(self):
        """Test creating category with attributes proper to it."""

        payload = {
            'name': 'Bags',
            'attributes': [
                {'name': 'color'},
                {'name': 'material'}
            ]
        }

        r = self.client.post(CATEGORIES_URL, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        category = Category.objects.get(id=r.data['id'])
        attributes = category.attributes.all()

        self.assertEqual(len(attributes), len(payload['attributes']))
        for attribute in payload['attributes']:
            exists = attributes.filter(name=attribute['name'].lower()).exists()
            self.assertTrue(exists)

    def test_get_single_category(self):
        cat = create_category(self.user)
        url = detail_url(cat.id)

        r = self.client.get(url)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['id'], cat.id)

    def test_update_category(self):
        cat = create_category(self.user)
        payload = {'name': 'Clothes'}

        url = detail_url(cat.id)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, payload['name'].lower())

    def test_update_category_with_attributes(self):
        """Test updating a category with attributes proper to it."""

        category = create_category(self.user)
        attr1 = Attribute.objects.create(
            user=self.user,
            name='a1'
        )
        payload = {
            'attributes': [
                {'name': 'color'},
                {'name': 'size'}
            ]
        }
        url = detail_url(category.id)

        r = self.client.patch(url, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        attributes = category.attributes.all()
        self.assertEqual(len(attributes), len(payload['attributes']))
        self.assertNotIn(attr1, attributes)

    def test_delete_category(self):
        cat = create_category(self.user)

        url = detail_url(cat.id)
        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

        exists = Category.objects.filter(id=cat.id).exists()
        self.assertFalse(exists)
