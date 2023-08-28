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
