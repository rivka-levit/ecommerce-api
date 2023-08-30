"""
Tests for brand APIs.
"""
from django.urls import reverse

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from product.models import Brand

BRANDS_URL = reverse('brand-list')


def detail_url(brand_id):
    return reverse('brand-detail', args=[brand_id])


def create_brand(**params):
    """Create and return a sample brand."""
    defaults = {
        'name': 'Sample Brand'
    }
    defaults.update(params)

    brand = Brand.objects.create(**defaults)

    return brand


class TestBrand(TestCase):
    """Tests for brand APIs."""
    def setUp(self) -> None:
        self.client = APIClient()

    def test_retrieve_brands_list(self):
        """Test retrieving the list of brands."""
        for _ in range(3):
            create_brand()

        r = self.client.get(BRANDS_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 3)

    def test_create_brand(self):
        """Test creating a brand via api"""
        payload = {'name': 'Nike'}

        r = self.client.post(BRANDS_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        brand = Brand.objects.get(id=r.data['id'])
        self.assertEqual(brand.name, payload['name'])

    def test_get_single_brand(self):
        """Test retrieving a single brand."""
        brand = create_brand()

        url = detail_url(brand.id)
        r = self.client.get(url)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['id'], brand.id)

    def test_update_brand(self):
        """Test updating a brand."""
        brand = create_brand(name='Nike')
        payload = {'name': 'Adidas'}

        url = detail_url(brand.id)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        brand.refresh_from_db()
        self.assertEqual(brand.name, payload['name'])

    def test_remove_brand(self):
        """Test removing a brand."""
        brand = create_brand()

        url = detail_url(brand.id)
        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

        exists = Brand.objects.filter(id=brand.id).exists()
        self.assertFalse(exists)