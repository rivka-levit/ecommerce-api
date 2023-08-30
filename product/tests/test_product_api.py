"""
Tests for product APIs.
"""
from django.urls import reverse

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from product.models import Product, Category, Brand
from product.serializers import ProductSerializer

PRODUCTS_URL = reverse('product-list')


def detail_url(product_id) -> str:
    """Return the url of detail pape for single product."""
    return reverse('product-detail', args=[product_id])


def create_product(**params) -> Product:
    """Create and return a sample product."""
    defaults = {
        'name': 'Sample Product',
        'description': 'Sample product description.'
    }
    defaults.update(params)

    return Product.objects.create(**defaults)


class TestProduct(TestCase):
    """Tests for product APIs."""
    def setUp(self) -> None:
        self.client = APIClient()

    def test_retrieve_product_list(self):
        """Test retrieving the list of products."""
        create_product()
        create_product()

        r = self.client.get(PRODUCTS_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)

    def test_create_simple_product(self):
        """Test creating a product without category or brand."""
        payload = {
            'name': 'Snickers',
            'description': 'Fashion snickers'
        }

        r = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        product = products[0]
        for k, v in payload.items():
            self.assertEqual(getattr(product, k), v)

    def test_get_product_detail(self):
        """Test retrieving a single product."""
        product = create_product()
        url = detail_url(product.id)

        r = self.client.get(url)
        serializer = ProductSerializer(product)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, serializer.data)

    def test_create_product_with_brand(self):
        """Test creating a product with brand."""
        payload = {
            'name': 'Snickers',
            'description': 'Fashion snickers',
            'brand': {'name': 'Nike'}
        }
        r = self.client.post(PRODUCTS_URL, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        product = products[0]
        self.assertEqual(product.brand.name, payload['brand']['name'])

    def test_create_product_with_category(self):
        """Test creating a product with category."""
        parent_category = Category.objects.create(name='Accessories')
        payload = {
            'name': 'Fashion Bag',
            'description': 'Great fashion bag from leather.',
            'category': {
                'name': 'Bags',
                'parent': parent_category.id,
            }
        }

        r = self.client.post(PRODUCTS_URL, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        product = products[0]
        self.assertEqual(product.category.name, payload['category']['name'])
        self.assertEqual(product.category.parent, parent_category)

    def test_update_product(self):
        """Test updating a product."""
        product = create_product()
        payload = {
            'brand': {'name': 'Desigual'},
            'category': {'name': 'Accessories'}
        }
        url = detail_url(product.id)
        r = self.client.patch(url, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.brand.name, payload['brand']['name'])
        self.assertEqual(product.category.name, payload['category']['name'])

    def test_delete_product(self):
        """Test removing a product."""
        product = create_product()
        url = detail_url(product.id)

        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        exists = Product.objects.filter(id=product.id).exists()
        self.assertFalse(exists)
