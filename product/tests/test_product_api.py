"""
Tests for product APIs.
"""
from django.urls import reverse
from django.contrib.auth import get_user_model

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from product.models import Product, Category, Brand, ProductLine, Attribute
from product.serializers import ProductSerializer

PRODUCTS_URL = reverse('product-list')


def detail_url(product_slug) -> str:
    """Return the url of detail pape for single product."""
    return reverse('product-detail', args=[product_slug])


def create_product(user, **params) -> Product:
    """Create and return a sample product."""
    defaults = {
        'name': 'Sample Product',
        'description': 'Sample product description.'
    }
    defaults.update(params)

    return Product.objects.create(user=user, **defaults)


class TestProductApi(TestCase):
    """Tests for product APIs."""
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test455@example.com',
            password='test_pass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_product_list(self):
        """Test retrieving the list of products."""
        create_product(self.user)
        create_product(self.user)

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
        product = create_product(self.user)
        url = detail_url(product.slug)

        r = self.client.get(url)
        serializer = ProductSerializer(product)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, serializer.data)

    def test_create_product_assign_brand(self):
        """Test creating a product with brand."""

        brand = Brand.objects.create(user=self.user, name='Nike')

        payload = {
            'name': 'Snickers',
            'description': 'Fashion snickers',
            'brand_slug': brand.slug
        }
        r = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        product = products[0]
        self.assertEqual(product.brand.slug, payload['brand_slug'])

    def test_create_product_assign_category(self):
        """Test creating a product with category."""
        parent_category = Category.objects.create(
            user=self.user,
            name='Accessories'
        )
        category = Category.objects.create(
            user=self.user,
            name='Bags',
            parent=parent_category)
        payload = {
            'name': 'Fashion Bag',
            'description': 'Great fashion bag from leather.',
            'category_slug': category.slug
        }

        r = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        product = products[0]
        self.assertEqual(product.category.slug, payload['category_slug'])
        self.assertEqual(product.category.parent, parent_category)

    def test_create_product_with_attributes(self):
        """Test creating product with attributes proper to it."""

        payload = {
            'name': 'Fashion Bag',
            'description': 'Great fashion bag from leather.',
            'attributes': [
                {
                    'name': 'color'
                },
                {
                    'name': 'material'
                }
            ]
        }

        r = self.client.post(PRODUCTS_URL, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        product = Product.objects.filter(
            name=payload['name'],
            description=payload['description']
        )
        self.assertTrue(product.exists())

        attributes = product[0].attributes.all()
        self.assertEqual(len(attributes), 2)

    def test_update_product(self):
        """Test updating a product."""
        product = create_product(self.user)
        brand = Brand.objects.create(user=self.user, name='Desigual')
        category = Category.objects.create(user=self.user, name='Accessories')
        payload = {
            'brand_slug': brand.slug,
            'category_slug': category.slug
        }
        url = detail_url(product.slug)
        r = self.client.patch(url, payload)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.brand, brand)
        self.assertEqual(product.category, category)

    def test_update_product_attributes(self):
        """Test updating attributes in a product."""

        product = create_product(self.user)
        attr1 = Attribute.objects.create(
            user=self.user,
            name='sample'
        )
        product.attributes.add(attr1)
        payload = {
            'attributes': [
                {'name': 'color'},
                {'name': 'size'}
            ]
        }
        url = detail_url(product.slug)

        r = self.client.patch(url, payload, format='json')

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.attributes.count(), 2)
        self.assertNotIn(attr1, product.attributes.all())

    def test_delete_product(self):
        """Test removing a product."""
        product = create_product(self.user)
        url = detail_url(product.slug)

        r = self.client.delete(url)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        exists = Product.objects.filter(id=product.id).exists()
        self.assertFalse(exists)

    def test_filter_products_by_category(self):
        """Test listing products and filtering it by category."""
        category1 = Category.objects.create(user=self.user, name='Cats')
        category2 = Category.objects.create(user=self.user, name='Dogs')
        create_product(user=self.user, category=category1)
        create_product(user=self.user, category=category2)
        create_product(user=self.user, category=category1)

        params = {'category_slug': category1.slug}
        r = self.client.get(PRODUCTS_URL, params)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)
        for item in r.data:
            self.assertEqual(item['category']['slug'], category1.slug)

    def test_filter_products_by_brand(self):
        """Test listing products and filtering it by brand."""
        brand1 = Brand.objects.create(user=self.user, name='Nike')
        brand2 = Brand.objects.create(user=self.user, name='Adidas')
        create_product(user=self.user, brand=brand2)
        create_product(user=self.user, brand=brand2)
        create_product(user=self.user, brand=brand1)

        params = {'brand': f'{brand2.name}'}
        r = self.client.get(PRODUCTS_URL, params)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 2)
        for item in r.data:
            self.assertEqual(item['brand']['name'], brand2.name)

    def test_retrieve_product_with_product_lines(self):
        """Test retrieving product liens when getting a product."""
        product = create_product(user=self.user)
        ProductLine.objects.create(
            user=self.user,
            product=product,
            sku=123,
            price='25.80',
            stock_qty=5
        )

        r = self.client.get(PRODUCTS_URL)
        self.assertEqual(len(r.data), 1)
        pr = r.data[0]
        self.assertEqual(len(pr['product_lines']), 1)
