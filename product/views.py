"""
Views for product APIs.
"""
from rest_framework import viewsets

from .models import Category, Brand
from product import serializers


class CategoryViewSet(viewsets.ModelViewSet):
    """View for managing category APIs."""
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class BrandViewSet(viewsets.ModelViewSet):
    """View for managing brand APIs."""
    queryset = Brand.objects.all()
    serializer_class = serializers.BrandSerializer
