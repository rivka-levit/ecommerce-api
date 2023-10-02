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


class AttributeSerializer(serializers.ModelSerializer):
    """Serializer for an attribute."""

    class Meta:
        model = Attribute
        fields = ['id', 'name']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories."""

    attributes = AttributeSerializer(many=True, required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'attributes']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create category with attributes."""

        attributes = validated_data.pop('attributes', [])

        category = Category.objects.create(**validated_data)

        for attribute in attributes:
            self._get_or_create_and_assign_attribute(
                attribute,
                Attribute,
                category
            )

        return category

    def update(self, instance, validated_data):
        """Update category with attributes."""

        attributes = validated_data.pop('attributes', [])

        instance.attributes.clear()

        for attribute in attributes:
            self._get_or_create_and_assign_attribute(
                attribute,
                Attribute,
                instance
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

    def _get_or_create_and_assign_attribute(self, attribute, model, category):
        """Get attribute if exists or create it, and assign to the category."""

        auth_user = self.context['request'].user
        attr_obj = get_or_create_parameter(auth_user, attribute, model)

        category.attributes.add(attr_obj)
        category.save()


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for brands."""

    class Meta:
        model = Brand
        fields = ['name', 'slug']
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


class AttributePatchSerializer(AttributeSerializer):
    """Serializer for list endpoint."""

    class Meta(AttributeSerializer.Meta):
        fields = ['id', 'name', 'description']


class VariationSerializer(serializers.ModelSerializer):
    """Serializer for a variation."""

    attribute = AttributeSerializer()

    class Meta:
        model = Variation
        fields = ['id', 'name', 'attribute']
        read_only_fields = ['id', 'attribute']


class VariationShortSerializer(VariationSerializer):
    """Short serializer for variation."""

    class Meta(VariationSerializer.Meta):
        fields = ['id', 'name']


class AttributeDetailSerializer(AttributeSerializer):
    """Serializer for an attribute for detail endpoints."""

    variations = VariationShortSerializer(many=True, required=False)
    # categories = CategorySerializer(many=True, required=False)

    class Meta(AttributeSerializer.Meta):
        fields = ['id', 'name', 'description', 'variations']

    def create(self, validated_data):
        """Create an attribute object."""

        auth_user = self.context['request'].user
        variations = validated_data.pop('variations', [])

        attribute = Attribute.objects.create(**validated_data)

        if variations:
            for v in variations:
                Variation.objects.create(
                    user=auth_user,
                    attribute=attribute,
                    name=v['name']
                )

        return attribute

    def update(self, instance, validated_data):
        """Update an attribute object."""

        auth_user = self.context['request'].user
        variations = validated_data.pop('variations', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if variations:
            for variation in instance.variations.all():
                variation.delete()

            for variation in variations:
                Variation.objects.create(
                    user=auth_user,
                    attribute=instance,
                    name=variation['name']
                )

        instance.save()
        return instance


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

    brand_slug = serializers.CharField(source='brand.slug', required=False)
    category_slug = serializers.CharField(
        source='category.slug',
        required=False
    )
    attributes = AttributeSerializer(many=True, required=False)
    product_lines = serializers.SerializerMethodField(
        'get_related_product_lines',
        required=False
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'slug', 'brand_slug', 'category_slug',
                  'is_digital', 'is_active', 'created_at', 'attributes',
                  'product_lines']
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

    def _get_or_create_and_assign_attribute(self, attribute, model, product):
        """Get attribute if exists or create it, and assign to the product."""

        auth_user = self.context['request'].user
        attr_obj = get_or_create_parameter(auth_user, attribute, model)

        product.attributes.add(attr_obj)
        product.save()

    @extend_schema_field(ProductLineSerializer(many=True))
    def get_related_product_lines(self, product):
        """Get the product lines of particular product"""

        qs = product.product_lines.filter(is_active=True).order_by('ordering')

        return ProductLineSerializer(qs, many=True).data

    def create(self, validated_data):
        """Create a product."""

        brand_slug = validated_data.pop('brand', None)
        category_slug = validated_data.pop('category', None)
        attributes = validated_data.pop('attributes', [])

        product = Product.objects.create(**validated_data)

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug['slug'])
            product.category = category

        if brand_slug:
            brand = get_object_or_404(Brand, slug=brand_slug['slug'])
            product.brand = brand

        product.save()

        # self._get_or_create_and_assign_brand(brand, Brand, product)
        # self._get_or_create_and_assign_category(category, Category, product)

        for attribute in attributes:
            self._get_or_create_and_assign_attribute(
                attribute,
                Attribute,
                product
            )

        return product

    def update(self, instance, validated_data):
        """Update a product."""

        brand_slug = validated_data.pop('brand', None)
        category_slug = validated_data.pop('category', None)
        attributes = validated_data.pop('attributes', [])

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug['slug'])
            instance.category = category

        if brand_slug:
            brand = get_object_or_404(Brand, slug=brand_slug['slug'])
            instance.brand = brand


        # self._get_or_create_and_assign_brand(brand, Brand, instance)
        # self._get_or_create_and_assign_category(category, Category, instance)

        instance.attributes.clear()

        for attribute in attributes:
            self._get_or_create_and_assign_attribute(
                attribute,
                Attribute,
                instance
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
