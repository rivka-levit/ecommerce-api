"""
URL configuration for product APIs.
"""
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('brands', views.BrandViewSet, basename='brand')
router.register('products', views.ProductViewSet, basename='product')
router.register('product-lines',
                views.ProductLineViewSet,
                basename='product-line'),
router.register('images', views.ProductImageViewSet, basename='image')
router.register('attributes', views.AttributeViewSet, basename='attribute')

urlpatterns = [
    path('', include(router.urls)),
]
