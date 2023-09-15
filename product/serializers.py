"""
Serializers for product APIs.
"""
from rest_framework import serializers

from .models import Category, Brand, Product, ProductLine


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


class ProductLineSerializer(serializers.ModelSerializer):
    """Serializer for product lines."""

    class Meta:
        model = ProductLine
        fields = ['sku', 'ordering', 'price', 'stock_qty', 'is_active']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""
    brand = BrandSerializer(required=False)
    category = CategorySerializer(required=False)
    product_lines = serializers.SerializerMethodField(
        'get_related_product_lines',
        required=False
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'slug', 'brand', 'category',
                  'is_digital', 'is_active', 'created_at', 'product_lines']
        read_only_fields = ['slug']

    def _get_or_create_and_assign_brand(self, brand, product):
        auth_user = self.context['request'].user
        if brand is not None:
            brand_obj, created = Brand.objects.get_or_create(
                user=auth_user,
                **brand
            )
            product.brand = brand_obj
            product.save()

    def _get_or_create_and_assign_category(self, category, product):
        auth_user = self.context['request'].user
        if category is not None:
            category_obj, created = Category.objects.get_or_create(
                user=auth_user,
                **category
            )
            product.category = category_obj
            product.save()

    def get_related_product_lines(self, product):
        """Get the product lines of particular product"""

        qs = product.product_lines.filter(is_active=True).order_by('-id')

        return ProductLineSerializer(qs, many=True).data

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
