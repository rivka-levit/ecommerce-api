"""
Views for product APIs.
"""
from rest_framework import viewsets

from .models import Category, Brand, Product
from product import serializers


class CategoryViewSet(viewsets.ModelViewSet):
    """View for managing category APIs."""
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class BrandViewSet(viewsets.ModelViewSet):
    """View for managing brand APIs."""
    queryset = Brand.objects.all()
    serializer_class = serializers.BrandSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """View for managing product APIs."""
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
