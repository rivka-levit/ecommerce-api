from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (Category, Brand, Product, ProductLine, ProductImage,
                     Attribute, Variation)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    readonly_fields = ['id']
    list_editable = ['is_active']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    readonly_fields = ['id']
    list_editable = ['is_active']


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['categories']


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ['name', 'attribute']


class VariationInLine(admin.TabularInline):
    model = Variation.product_lines.through
    extra = 0


class EditLinkInLine(object):
    """Create a link to upload images inline."""

    def edit(self, instance):
        """Return a link to edit image if the instance exists."""

        url = reverse(
            f'admin:{instance._meta.app_label}_'
            f'{instance._meta.model_name}_change',
            args=[instance.pk]
        )

        if instance.pk:
            return mark_safe(f'<a href="{url}">Edit</a>')
        return ''


class ProductLineInline(EditLinkInLine, admin.TabularInline):
    model = ProductLine
    fields = ['user', 'sku', 'price', 'stock_qty', 'ordering',
              'edit', 'is_active']
    extra = 0
    readonly_fields = ['edit']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'created_at', 'is_active']
    readonly_fields = ['id', 'created_at']
    list_editable = ['is_active']
    inlines = [ProductLineInline]


class ProductImageInLine(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = ['user', 'sku', 'price', 'stock_qty', 'ordering',
                    'is_active']
    inlines = [ProductImageInLine, VariationInLine]
