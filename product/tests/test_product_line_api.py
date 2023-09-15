"""
Tests for product lines APIs.
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from product.models import Product, ProductLine
from product.serializers import ProductLineSerializer


def create_product(user, **kwargs):
    """Create a sample product."""

    defaults = {
        'name': 'Sample Product',
        'description': 'Sample product description.'
    }
    defaults.update(kwargs)

    return Product.objects.create(user=user, **defaults)


def create_product_line(user, product, sku, **kwargs):
    """Create a sample product line."""
    defaults = {
        'price': 100,
        'stock_qty': 35,
    }
    defaults.update(**kwargs)

    return ProductLine.objects.create(
        user=user,
        product=product,
        sku=sku,
        **defaults
    )


class ProductLineApiTests(TestCase):
    """Tests for product lines APIs."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test_pr_liens_user@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)
        self.product = create_product(self.user)

    def test_product_line_create_successful(self):
        """Test creating a product line successfully."""

        payload = {
            'sku': 'red',
            'price': 53,
            'stock_qty': 10
        }

        url = reverse('product-line-create', args=[self.product.slug])
        r = self.client.post(url, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        product_line = ProductLine.objects.get(
            sku=payload['sku'],
            product=self.product
        )
        serializer = ProductLineSerializer(product_line)

        self.assertEqual(r.data, serializer.data)

    def test_product_line_update_successful(self):
        """Test updating a product line of a particular product."""

        product_line = create_product_line(self.user, self.product, 'beige')

        payload = {
            'sku': 'aquamarine'
        }

        url = reverse(
            'product-line-update',
            args=[self.product.slug,
                  product_line.sku]
        )
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        product_line.refresh_from_db()
        self.assertEqual(product_line.sku, payload['sku'])

    def test_product_line_delete_successful(self):
        """Test deleting a product line."""

        product_line = create_product_line(self.user, self.product, 'bamboo')

        url = reverse(
            'product-line-delete',
            args=[self.product.slug, product_line.sku]
        )

        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        exists = ProductLine.objects.filter(
            user=self.user,
            product=self.product,
            sku=product_line.sku
        ).exists()
        self.assertFalse(exists)

    def test_create_product_line_with_ordering_number(self):
        """Create and retrieve ordering number automatically when creating
        a product line."""

        payload = {
            'sku': 'compose-5',
            'price': '538',
            'stock_qty': 15
        }

        url = reverse('product-line-create', args=[self.product.slug])
        r = self.client.post(url, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn('ordering', r.data)
        self.assertEqual(r.data['ordering'], 1)
