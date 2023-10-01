from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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


def create_product_line(**params) -> models.ProductLine:
    """Create and return a sample product line."""
    defaults = {
        'sku': 'sample_sku',
        'price': '100',
        'stock_qty': 35
    }
    defaults.update(**params)

    return models.ProductLine.objects.create(**defaults)


def create_attribute(user, **params):
    """Create and return a sample attribute."""
    defaults = {
        'name': 'color',
        'description': 'Sample description.'
    }
    defaults.update(**params)

    return models.Attribute.objects.create(user=user, **defaults)


class ModelTests(TestCase):
    """Tests for models."""

    def setUp(self) -> None:
        self.user = create_user()

    def test_create_category_without_parent(self):
        category = models.Category.objects.create(
            name='Shoes',
            user=self.user
        )

        self.assertEqual(category.name, 'shoes')
        self.assertEqual(str(category), 'shoes')

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

        self.assertEqual(brand.name, 'nike')
        self.assertEqual(str(brand), 'nike')

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

    def test_create_product_generate_slug(self):
        """Test generating slug automatically when a product is created."""
        product = create_product(user=self.user)

        self.assertTrue(product.slug)

    def test_product_attributes_assigned_success(self):
        """Test assigning attributes to a product."""

        a1 = create_attribute(self.user)
        a2 = create_attribute(self.user, name='size')
        a3 = create_attribute(self.user, name='resolution')

        product = create_product(user=self.user)
        product.attributes.add(a1)
        product.attributes.add(a2)

        product.refresh_from_db()
        product_attributes = product.attributes.all()

        self.assertIn(a1, product_attributes)
        self.assertIn(a2, product_attributes)
        self.assertNotIn(a3, product_attributes)

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


class ProductLineModelTests(TestCase):
    """Tests for the ProductLine model."""

    def setUp(self) -> None:
        self.user = create_user()
        self.product = create_product(user=self.user)

    def test_create_product_line_ordering_auto_add(self):
        """
        Test adding the order number to the ordering fild automatically,
        when creating a product line
        """

        pl1 = create_product_line(
            product=self.product,
            user=self.user,
            sku='first'
        )
        pl2 = create_product_line(
            product=self.product,
            user=self.user,
            sku='second'
        )

        self.assertEqual(pl1.ordering, 1)
        self.assertEqual(pl2.ordering, 2)

    def test_create_product_line_add_ordering_manually(self):
        """Test adding custom order number successfully when creating
        a product line."""

        pl1 = create_product_line(
            product=self.product,
            user=self.user,
            sku='first',
            ordering=3
        )

        self.assertEqual(pl1.ordering, 3)

    def test_not_unique_ordering_raise_error(self):
        """Test raising ValidationError if creating a product line with
        not unique ordering number."""

        create_product_line(
            product=self.product,
            user=self.user,
            sku='first',
            ordering=1
        )

        with self.assertRaises(ValidationError):
            create_product_line(
                product=self.product,
                user=self.user,
                sku='second',
                ordering=1
            )

        qs = self.product.product_lines.all()
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs[0].sku, 'first')


class AttributesModelsTests(TestCase):
    """Tests for the models of Attribute, Variation, ProductLineVariation."""

    def setUp(self) -> None:
        self.user = create_user(email='attr_test@example.com')
        self.product = create_product(user=self.user)
        self.product_line = create_product_line(
            user=self.user,
            product=self.product
        )

    def test_create_attribute_success(self):
        """Test creating an attribute"""

        payload = {
            'name': 'size',
            "description": 'Sample description',
        }

        attribute = create_attribute(user=self.user, **payload)

        for k, v in payload.items():
            self.assertEqual(getattr(attribute, k), payload[k])

    def test_create_attribute_assigned_to_category(self):
        """Test creating an attribute and assigning it to a category."""

        category = models.Category.objects.create(user=self.user, name='Bags')
        attribute = create_attribute(self.user, name='Color')

        attribute.categories.add(category)
        category.refresh_from_db()

        self.assertIn(category, attribute.categories.all())

    def test_filter_attributes_by_category(self):
        """Test filtering attributes by category."""

        category = models.Category.objects.create(user=self.user, name='Bags')

        attr_1 = create_attribute(self.user, name='Color')
        attr_2 = create_attribute(self.user, name='Resolution')

        attr_1.categories.add(category)
        attr_1.refresh_from_db()

        attributes = models.Attribute.objects.filter(categories__in=(category,))

        self.assertIn(attr_1, attributes)
        self.assertNotIn(attr_2, attributes)

    def test_create_variations(self):
        """Test creating variations of an attribute"""

        payload = {'name': 'red'}

        attribute = create_attribute(self.user)
        variation = models.Variation.objects.create(
            user=self.user,
            attribute=attribute,
            **payload
        )

        self.assertIsInstance(variation, models.Variation)
        self.assertEqual(variation.name, payload['name'])

    def test_create_product_line_variation(self):
        """
        Test creating a variation of an attribute that belongs to a
        particular product line.
        """
        attribute = create_attribute(self.user)

        payload = {
            'user': self.user,
            'attribute': attribute,
            'name': 'red'
        }

        variation = models.Variation.objects.create(**payload)

        pl_variation = models.ProductLineVariation(
            user=self.user,
            variation=variation,
            product_line=self.product_line
        )

        self.assertIsInstance(pl_variation, models.ProductLineVariation)
        self.assertEqual(pl_variation.variation, variation)
        self.assertEqual(pl_variation.product_line, self.product_line)

    def test_product_line_contains_its_variations(self):
        """
        Test product line retrieves just the variations of this
        product line.
        """

        attribute = create_attribute(self.user)
        pl_2 = create_product_line(
            user=self.user,
            product=self.product,
            sku='another product line'
        )

        v1 = models.Variation.objects.create(
            user=self.user,
            attribute=attribute,
            name='red'
        )
        v2 = models.Variation.objects.create(
            user=self.user,
            attribute=attribute,
            name='blue'
        )

        models.ProductLineVariation.objects.create(
            user=self.user,
            variation=v1,
            product_line=self.product_line
        )

        models.ProductLineVariation.objects.create(
            user=self.user,
            variation=v2,
            product_line=pl_2
        )

        self.product_line.refresh_from_db()
        pl_2.refresh_from_db()

        self.assertIn(v1, self.product_line.variations.all())
        self.assertIn(v2, pl_2.variations.all())
        self.assertNotIn(v1, pl_2.variations.all())
        self.assertNotIn(v2, self.product_line.variations.all())
