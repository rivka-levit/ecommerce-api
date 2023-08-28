from django.test import TestCase

from product import models


class ModelTests(TestCase):
    """Tests for models."""
    def test_create_category(self):
        category = models.Category.objects.create(name='Shoes')

        self.assertEqual(category.name, 'Shoes')
        self.assertEqual(str(category), 'Shoes')

    def test_create_brand(self):
        brand = models.Brand.objects.create(name='Nike')

        self.assertEqual(brand.name, 'Nike')
        self.assertEqual(str(brand), 'Nike')

    def test_create_product(self):
        category = models.Category.objects.create(name='Shoes')
        brand = models.Brand.objects.create(name='Nike')
        payload = {
            'name': 'Snickers',
            'brand': brand,
            'description': 'Sample snickers description.'
        }
        product = models.Product.objects.create(**payload)
        product.category.add(category)

        for k, v in payload:
            self.assertEqual(product.getattr(k), v)

        self.assertIn(category, product.category.all())
        self.assertFalse(product.is_digital)
        self.assertTrue(product.is_active)
