"""
Serializers for product APIs.
"""
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from .models import (Category, Brand, Product, ProductLine, ProductImage,
                     Attribute, Variation)


def get_or_create_parameter(user, param_data, model):
    """Get or create an object of model."""

    if param_data is not None:
        param_data['name'] = param_data['name'].lower()
        param_obj, created = model.objects.get_or_create(
            user=user,
            **param_data
        )

        return param_obj


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


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""

    class Meta:
        model = ProductImage
        fields = ['id', 'alt_text', 'image', 'ordering']
        read_only_fields = ['id']


class CreateProductImageSerializer(ProductImageSerializer):
    """Serializer for creating product images."""

    product_line_id = serializers.IntegerField(
        source='product_line.id',
        required=True
    )

    class Meta(ProductImageSerializer.Meta):
        fields = ['id', 'alt_text', 'ordering', 'product_line_id']

    def create(self, validated_data):
        """Create and return image object."""
        product_line_id = validated_data.pop('product_line')['id']

        product_line = get_object_or_404(
            ProductLine,
            id=product_line_id
        )

        image = ProductImage.objects.create(
            product_line=product_line,
            **validated_data
        )

        return image


class UpdateImageSerializer(ProductImageSerializer):
    """Serializer for updating an image object."""

    class Meta(ProductImageSerializer.Meta):
        fields = ['id', 'alt_text', 'ordering']


class UploadImageSerializer(ProductImageSerializer):
    """Serializer for uploading images to image objects."""

    class Meta(ProductImageSerializer.Meta):
        fields = ['id', 'image']


class AttributeSerializer(serializers.ModelSerializer):
    """Serializer for an attribute."""

    class Meta:
        model = Attribute
        fields = ['id', 'name']


class AttributeDetailSerializer(AttributeSerializer):
    """Serializer for an attribute for detail endpoints."""

    categories = CategorySerializer(many=True, required=False)

    class Meta(AttributeSerializer.Meta):
        fields = ['id', 'name', 'description', 'categories']

    def create(self, validated_data):
        """Create an attribute object."""

        auth_user = self.context['request'].user
        categories = validated_data.pop('categories', [])

        attribute = Attribute.objects.create(**validated_data)

        if categories:
            for category in categories:
                cat = get_or_create_parameter(auth_user, category, Category)
                attribute.categories.add(cat)

        return attribute

    def update(self, instance, validated_data):
        """Update an attribute object."""

        auth_user = self.context['request'].user
        categories = validated_data.pop('categories', [])

        if categories:
            for category in categories:
                cat = get_or_create_parameter(auth_user, category, Category)
                if cat not in instance.categories.all():
                    instance.categories.add(cat)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class VariationSerializer(serializers.ModelSerializer):
    """Serializer for a variation."""

    attribute = AttributeSerializer()

    class Meta:
        model = Variation
        fields = ['id', 'attribute', 'name']


class CreateUpdateDeleteVariationSerializer(VariationSerializer):
    """
    Serializer to create, update and delete variation through
    attribute view set.
    """

    class Meta(VariationSerializer.Meta):
        fields = ['id', 'name']


class ProductLineSerializer(serializers.ModelSerializer):
    """Serializer for product lines."""

    images = ProductImageSerializer(many=True, required=False)
    variations = VariationSerializer(many=True, required=False)

    class Meta:
        model = ProductLine
        fields = ['id', 'sku', 'ordering', 'price', 'stock_qty', 'is_active',
                  'images', 'variations']
        read_only_fields = ['id']


class CreateProductLineSerializer(serializers.ModelSerializer):
    """Serializer for creating product lines."""

    product_slug = serializers.CharField(source='product.slug', required=True)

    class Meta:
        model = ProductLine
        fields = ['product_slug', 'sku', 'ordering', 'price', 'stock_qty',
                  'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        auth_user = self.context['request'].user
        product_slug = validated_data.pop('product')['slug']
        product = get_object_or_404(
            Product,
            slug=product_slug,
            user=auth_user
        )

        product_line = ProductLine.objects.create(
            product=product,
            **validated_data
        )

        return product_line


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

    def _get_or_create_and_assign_brand(self, brand, model, product):
        """Get brand if exists or create it, and assign to the product."""

        auth_user = self.context['request'].user
        brand_obj = get_or_create_parameter(auth_user, brand, model)

        product.brand = brand_obj
        product.save()

    def _get_or_create_and_assign_category(self, category, model, product):
        """Get category if exists or create it, and assign to the product."""

        auth_user = self.context['request'].user
        category_obj = get_or_create_parameter(auth_user, category, model)

        product.category = category_obj
        product.save()

    @extend_schema_field(ProductLineSerializer(many=True))
    def get_related_product_lines(self, product):
        """Get the product lines of particular product"""

        qs = product.product_lines.filter(is_active=True).order_by('ordering')

        return ProductLineSerializer(qs, many=True).data

    def create(self, validated_data):
        """Create a product."""

        brand = validated_data.pop('brand', None)
        category = validated_data.pop('category', None)

        product = Product.objects.create(**validated_data)

        self._get_or_create_and_assign_brand(brand, Brand, product)
        self._get_or_create_and_assign_category(category, Category, product)

        return product

    def update(self, instance, validated_data):
        """Update a product."""

        brand = validated_data.pop('brand', None)
        category = validated_data.pop('category', None)

        self._get_or_create_and_assign_brand(brand, Brand, instance)
        self._get_or_create_and_assign_category(category, Category, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
