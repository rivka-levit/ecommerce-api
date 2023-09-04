from django.test import TestCase
from django.contrib.auth import get_user_model

from product import models


def create_user(email='test@example.con', password='test_pass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email, password)


def create_product(**params) -> models.Product:
    """Create and return a sample product"""
    defaults = {
        'name': 'Sample product name',
        'description': 'Sample product description.'
    }
    defaults.update(params)

    product = models.Product.objects.create(**defaults)

    return product


class ModelTests(TestCase):
    """Tests for models."""

    def setUp(self) -> None:
        self.user = create_user()

    def test_create_category_without_parent(self):
        category = models.Category.objects.create(
            name='Shoes',
            user=self.user
        )

        self.assertEqual(category.name, 'Shoes')
        self.assertEqual(str(category), 'Shoes')

    def test_create_category_with_parent(self):
        category = models.Category.objects.create(
            name='Clothes',
            user=self.user
        )
        sub_category = models.Category.objects.create(
            name='Shoes',
            parent=category,
            user=self.user
        )
        self.assertIn(sub_category, category.children.all())

    def test_create_three_categories_to_same_parent(self):
        parent_category = models.Category.objects.create(
            user=self.user,
            name='Parent'
        )
        cat1 = models.Category.objects.create(
            user=self.user,
            name='Cat1',
            parent=parent_category
        )
        cat2 = models.Category.objects.create(
            user=self.user,
            name='Cat2',
            parent=parent_category
        )
        cat3 = models.Category.objects.create(
            user=self.user,
            name='Cat3',
            parent=parent_category
        )
        for cat in (cat1, cat2, cat3):
            self.assertEqual(cat.parent, parent_category)
            parent_category.refresh_from_db()
            self.assertEqual(parent_category.children.count(), 3)

    def test_delete_parent_category_set_null_to_children(self):
        """Test deleting a category and assign None value to its children"""

        parent_category = models.Category.objects.create(
            user=self.user,
            name='Parent'
        )
        child1 = models.Category.objects.create(
            user=self.user,
            name='ch1',
            parent=parent_category
        )
        child2 = models.Category.objects.create(
            user=self.user,
            name='ch2',
            parent=parent_category
        )

        parent_category.delete()

        child1.refresh_from_db()
        child2.refresh_from_db()
        self.assertEqual(child1.parent, None)
        self.assertEqual(child2.parent, None)

    def test_create_brand(self):
        brand = models.Brand.objects.create(name='Nike', user=self.user)

        self.assertEqual(brand.name, 'Nike')
        self.assertEqual(str(brand), 'Nike')

    def test_create_product(self):
        brand = models.Brand.objects.create(name='Nike', user=self.user)
        category = models.Category.objects.create(name='Shoes', user=self.user)
        payload = {
            'name': 'Snickers',
            'brand': brand,
            'category': category,
            'description': 'Sample snickers description.'
        }
        # product = models.Product.objects.create(**payload)
        product = create_product(user=self.user, **payload)

        self.assertEqual(str(product), payload['name'])

        for k, v in payload.items():
            self.assertEqual(getattr(product, k), v)

        self.assertFalse(product.is_digital)
        self.assertTrue(product.is_active)

    def test_create_product_line_success(self):
        """Test creating a product line for a product successful."""

        brand = models.Brand.objects.create(name='Desigual', user=self.user)
        category = models.Category.objects.create(name='Bags', user=self.user)

        product = models.Product.objects.create(
            name='Fashion bag',
            description='',
            user=self.user,
            brand=brand,
            category=category
        )

        data = {
            'user': self.user,
            'price': '580.00',
            'sku': 'bag9877wer',
            'stock_qty': 38,
            'product': product
        }

        product_line = models.ProductLine.objects.create(**data)

        self.assertEqual(str(product_line), data['sku'])
        self.assertEqual(product_line.stock_qty, data['stock_qty'])
