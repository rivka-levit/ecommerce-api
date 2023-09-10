"""
Tests for product lines APIs.
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from product.models import Product, ProductLine

PRODUCT_LINES_URL = reverse('product-line-list')


def detail_url(obj_id):
    """Return the url of a particular product line."""

    return reverse('product-line-detail', args=[obj_id])


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

    def test_product_line_list_without_product_fails(self):
        """Test retrieving product lines fails for without product."""

        r = self.client.get(PRODUCT_LINES_URL)

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_line_list_with_product_success(self):
        """Test retrieving product liens assigned to a product successful."""

        product = create_product(self.user)
        create_product_line(self.user, product, 'red')
        create_product_line(self.user, product, 'blue')
        params = {'product': product.slug}

        r = self.client.get(PRODUCT_LINES_URL, params)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)
