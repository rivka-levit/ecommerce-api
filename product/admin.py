from django.contrib import admin
from .models import Category, Brand, Product


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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'created_at', 'is_active']
    readonly_fields = ['id', 'created_at']
    list_editable = ['is_active']
