"""
Serializers for product APIs.
"""
from rest_framework import serializers

from .models import Category, Brand, Product


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']
        read_only_fields = ['id']


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for brands."""
    class Meta:
        model = Brand
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""
    brand = BrandSerializer(required=False)
    category = CategorySerializer(required=False)

    class Meta:
        model = Product
        fields = ['name', 'description', 'brand', 'category', 'is_digital',
                  'is_active', 'created_at']
        read_only_fields = ['id']

    def _get_or_create_and_assign_brand(self, brand, product):
        if brand is not None:
            brand_obj, created = Brand.objects.get_or_create(**brand)
            product.brand = brand_obj
            product.save()

    def _get_or_create_and_assign_category(self, category, product):
        if category is not None:
            category_obj, created = Category.objects.get_or_create(**category)
            product.category = category_obj
            product.save()

    def create(self, validated_data):
        """Create a product."""
        brand = validated_data.pop('brand', None)
        category = validated_data.pop('category', None)

        product = Product.objects.create(**validated_data)

        self._get_or_create_and_assign_brand(brand, product)
        self._get_or_create_and_assign_category(category, product)

        return product

    def update(self, instance, validated_data):
        """Update a product."""
        brand = validated_data.pop('brand', None)
        category = validated_data.pop('category', None)

        self._get_or_create_and_assign_brand(brand, instance)
        self._get_or_create_and_assign_category(category, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
