from django.test import TestCase

from product import models


class ModelTests(TestCase):
    """Tests for models."""
    def test_create_category(self):
        category = models.Category(name='Shoes')

        self.assertEqual(category.name, 'Shoes')
        self.assertEqual(str(category), 'Shoes')
