"""
Tests for product lines APIs.
"""
import tempfile
import os

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from PIL import Image

from product.models import Product, ProductLine
from product.serializers import ProductLineSerializer, CreateProductLineSerializer

PRODUCT_LINES_URL = reverse('product-line-list')
IMAGES_URL = reverse('image-list')


def pl_detail_url(item_id):
    return reverse('product-line-detail', args=[item_id])


def image_detail_url(item_id):
    return reverse('image-detail', args=[item_id])


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
            email='test_pr_lines_user@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)
        self.product = create_product(self.user)

    def test_product_line_create_successful(self):
        """Test creating a product line successfully."""

        payload = {
            'product_slug': self.product.slug,
            'sku': 'red',
            'price': 53,
            'stock_qty': 10
        }

        r = self.client.post(PRODUCT_LINES_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        product_line = ProductLine.objects.get(
            sku=payload['sku'],
            product=self.product
        )
        serializer = CreateProductLineSerializer(product_line)

        self.assertEqual(r.data, serializer.data)

    def test_product_line_update_successful(self):
        """Test updating a product line of a particular product."""

        product_line = create_product_line(self.user, self.product, 'beige')

        payload = {
            'sku': 'aquamarine'
        }

        url = pl_detail_url(product_line.id)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        product_line.refresh_from_db()
        self.assertEqual(product_line.sku, payload['sku'])

    def test_product_line_delete_successful(self):
        """Test deleting a product line."""

        product_line = create_product_line(self.user, self.product, 'bamboo')

        url = pl_detail_url(product_line.id)

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
            'product_slug': self.product.slug,
            'sku': 'compose-5',
            'price': '538',
            'stock_qty': 15
        }

        r = self.client.post(PRODUCT_LINES_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn('ordering', r.data)
        self.assertEqual(r.data['ordering'], 1)

    def test_create_product_line_custom_ordering_number_success(self):
        """Test creating a product line with custom ordering number."""

        payload = {
            'product_slug': self.product.slug,
            'sku': 'krak-krak-8',
            'ordering': 5,
            'price': '58',
            'stock_qty': 3,
        }

        r = self.client.post(PRODUCT_LINES_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['ordering'], payload['ordering'])

    def test_create_product_line_duplicate_ordering_error(self):
        """
        Test raising an error when creating a product line with duplicated
        ordering number.
        """

        create_product_line(self.user, self.product, 'some_sku', ordering=3)
        payload = {
            'product_slug': self.product.slug,
            'sku': 'krak-krak-8',
            'price': '300',
            'stock_qty': 38,
            'ordering': 3
        }

        with self.assertRaises(ValidationError):
            self.client.post(PRODUCT_LINES_URL, payload)


class ProductImageApiTests(TestCase):
    """Tests for product image APIs."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test_image_user@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)
        self.product = create_product(self.user)
        self.product_line = create_product_line(
            self.user,
            self.product,
            'kappa-poo')

    def tearDown(self) -> None:
        images = self.product_line.images.all()
        for image in images:
            image.delete()

    def test_create_upload_image(self):
        """Test creating an image object and upload the image itself."""

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new(mode='RGB', size=(10, 10))
            img.save(image_file, format='JPEG')
            img.seek(0)

            payload = {
                'user': self.user,
                'alt_text': 'some_image',
                'image': image_file,
                'product_line': self.product_line
            }

            r = self.client.post(IMAGES_URL, payload, format='multipart')

        self.product_line.refresh_from_db()

        self.assertEqual(r.status_code, status.HTTP_200_OK)

        images = self.product_line.images.all()

        self.assertEqual(len(images), 1)
        self.assertTrue(os.path.exists(images[0].image.path))
