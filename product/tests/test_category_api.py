"""
Tests for Category APIs.
"""
from django.urls import reverse

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from product.models import Category

CATEGORIES_URL = reverse('product:category-list')


def detail_url(category_id):
    """Create and return the url of detail page."""
    return reverse('product:category-detail', args=[category_id])


def create_category():
    """Create a sample category for testing purposes."""
    return Category.objects.create(name='Sample Name')


class TestCategoryApi(TestCase):
    """Tests for category APIs."""
    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_category_list(self):
        """Test retrieving the list of categories."""
        create_category()
        create_category()

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
        self.assertEqual(category.name, payload['name'])

    def test_get_single_category(self):
        cat = create_category()
        url = detail_url(cat.id)

        r = self.client.get(url)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['id'], cat.id)

    def test_update_category(self):
        cat = create_category()
        payload = {'name': 'Clothes'}

        url = detail_url(cat.id)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, payload['name'])

    def test_delete_category(self):
        cat = create_category()

        url = detail_url(cat.id)
        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

        exists = Category.objects.filter(id=cat.id).exists()
        self.assertFalse(exists)
