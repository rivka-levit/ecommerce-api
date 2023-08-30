"""
URL configuration for product APIs.
"""
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

app_name = 'store'

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls))
]
