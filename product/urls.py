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

urlpatterns = [
    path('', include(router.urls)),
    path(
        '<slug:product_slug>/product-line/create/',
        views.ProductLineView.as_view(),
        name='product-line-create'
    ),
    path(
        '<slug:product_slug>/product-line/<sku>/',
        views.ProductLineView.as_view(),
        name='product-line-update'
    ),
]
