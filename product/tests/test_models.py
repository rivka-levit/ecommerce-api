from django.test import TestCase

from product import models


class ModelTests(TestCase):
    """Tests for models."""
    def test_create_category_without_parent(self):
        category = models.Category.objects.create(name='Shoes')

        self.assertEqual(category.name, 'Shoes')
        self.assertEqual(str(category), 'Shoes')

    def test_create_category_with_parent(self):
        category = models.Category.objects.create(name='Clothes')
        sub_category = models.Category.objects.create(
            name='Shoes',
            parent=category
        )
        self.assertIn(sub_category, category.children.all())

    def test_create_brand(self):
        brand = models.Brand.objects.create(name='Nike')

        self.assertEqual(brand.name, 'Nike')
        self.assertEqual(str(brand), 'Nike')

    def test_create_product(self):
        brand = models.Brand.objects.create(name='Nike')
        payload = {
            'name': 'Snickers',
            'brand': brand,
            'description': 'Sample snickers description.'
        }
        product = models.Product.objects.create(**payload)

        for k, v in payload.items():
            self.assertEqual(getattr(product, k), v)

        self.assertFalse(product.is_digital)
        self.assertTrue(product.is_active)
