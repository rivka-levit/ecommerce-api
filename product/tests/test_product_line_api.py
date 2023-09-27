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

from product.models import (Product, ProductLine, ProductImage, Attribute,
                            Variation, ProductLineVariation)
from product.serializers import CreateProductLineSerializer

PRODUCT_LINES_URL = reverse('product-line-list')
IMAGES_URL = reverse('image-list')


def pl_detail_url(item_id):
    return reverse('product-line-detail', args=[item_id])


def image_detail_url(image_id):
    return reverse('image-detail', args=[image_id])


def upload_image_url(image_id):
    return reverse('image-upload-image', args=[image_id])


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


def create_image(user, product_line, **kwargs):
    """Create and return a sample image object."""

    defaults = {
        'alt_text': 'some alternative text',
        'image': 'test_imag.jpg',
    }
    defaults.update(**kwargs)

    return ProductImage.objects.create(
        user=user,
        product_line=product_line,
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


class ProductLineVariationsApiTests(TestCase):
    """Tests for APIs that manage variations in product lines."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test_pr_lines_user@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)
        self.product = create_product(self.user)
        self.product_line = create_product_line(
            self.user,
            self.product,
            'with chain'
        )
        self.attribute = Attribute.objects.create(
            user=self.user,
            name='color'
        )
        self.variation = Variation.objects.create(
            user=self.user,
            attribute=self.attribute,
            name='red'
        )

    def test_attach_product_line_variation(self):
        """Test assigning variation to a product line."""

        url = reverse(
            'product-line-attach-variation',
            args=[self.product_line.id, self.variation.id]
        )

        r = self.client.post(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.product_line.refresh_from_db()
        self.assertIn(self.variation, self.product_line.variations.all())

    def test_detach_product_line_variation(self):
        """Test detaching variation from a product line."""

        ProductLineVariation.objects.create(
            user=self.user,
            product_line=self.product_line,
            variation=self.variation
        )
        self.product_line.refresh_from_db()

        self.assertIn(self.variation, self.product_line.variations.all())

        url = reverse(
            'product-line-detach-variation',
            args=[self.product_line.id, self.variation.id]
        )

        r = self.client.post(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.product_line.refresh_from_db()
        self.assertNotIn(self.variation, self.product_line.variations.all())


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
        for image_obj in images:
            image_obj.image.delete()

    def test_create_image_object(self):
        """Test creating image object without the image itself."""

        payload = {
            'alt_text': 'some_image',
            'product_line_id': self.product_line.id
        }

        r = self.client.post(IMAGES_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_upload_image(self):
        """Test creating an image object and upload the image itself."""

        image_obj = create_image(self.user, self.product_line)
        url = upload_image_url(image_obj.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}

            r = self.client.post(url, payload, format='multipart')

        self.product_line.refresh_from_db()

        self.assertEqual(r.status_code, status.HTTP_200_OK)

        images = self.product_line.images.all()

        self.assertEqual(len(images), 1)
        self.assertTrue(os.path.exists(images[0].image.path))

    def test_update_image_success(self):
        """Test updating image successfully."""

        img = create_image(self.user, self.product_line)

        payload = {
            'alt_text': 'new text',
            'product_line_id': self.product_line.id
        }

        url = image_detail_url(img.id)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)

        img.refresh_from_db()
        self.assertEqual(img.alt_text, payload['alt_text'])

    def test_remove_image(self):
        """Test removing an image from product line."""

        img = create_image(self.user, self.product_line)

        url = image_detail_url(img.id)
        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

        self.product_line.refresh_from_db()
        images = self.product_line.images.filter(
            user=self.user,
            product_line=self.product_line
        )
        self.assertFalse(images.exists())
