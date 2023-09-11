"""
Views for product APIs.
"""
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes
)

from .models import Category, Brand, Product, ProductLine
from product import serializers


class BaseStoreViewSet(viewsets.ModelViewSet):
    """Base view set for product app APIs."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve products for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        """Create a new product assigned to the user."""
        serializer.save(user=self.request.user)


class CategoryViewSet(BaseStoreViewSet):
    """View for managing category APIs."""
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class BrandViewSet(BaseStoreViewSet):
    """View for managing brand APIs."""
    queryset = Brand.objects.all()
    serializer_class = serializers.BrandSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'category',
                OpenApiTypes.STR,
                description='Category name',
                required=False
            ),
            OpenApiParameter(
                'brand',
                OpenApiTypes.STR,
                description='Brand name',
                required=False
            )
        ]
    )
)
class ProductViewSet(BaseStoreViewSet):
    """View for managing product APIs."""
    queryset = Product.objects.all().select_related('category', 'brand')
    serializer_class = serializers.ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        """Retrieve products, filtering them by category."""
        category_name = self.request.query_params.get('category')
        brand_name = self.request.query_params.get('brand')

        queryset = super().get_queryset()

        if category_name:
            queryset = queryset.filter(
                category__name=category_name
            ).order_by('-id').distinct()

        if brand_name:
            queryset = queryset.filter(
                brand__name=brand_name
            ).order_by('-id').distinct()

        return queryset


@extend_schema(
    request=serializers.ProductLineSerializer,
    responses={201: serializers.ProductLineSerializer}
)
class ProductLineView(APIView):
    """View for managing product line APIs."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def _get_product(self, user, product_slug) -> Product | Response:
        """Return product or error response."""
        try:
            product = Product.objects.get(user=user, slug=product_slug)
        except Product.DoesNotExist:
            return Response(
                {'message': 'Invalid product slug. Product does not exist.'}
            )
        return product

    def post(self, request, product_slug):
        """Create a new product line for a particular product."""

        auth_user = self.request.user

        product = self._get_product(auth_user, product_slug)

        serializer = serializers.ProductLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=auth_user, product=product)

            product_line = ProductLine.objects.get(
                user=auth_user,
                product=product,
                sku=serializer.data['sku']
            )

            return Response(
                serializers.ProductLineSerializer(product_line).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, product_slug, sku):
        """Partial update of a product line."""

        auth_user = self.request.user

        product = Product.objects.get(user=auth_user, slug=product_slug)

        product_line = ProductLine.objects.get(
            user=auth_user,
            product=product,
            sku=sku
        )

        # Update all the fields that have been passed with the request.
        for k, v in request.data.items():
            setattr(product_line, k, v)

        product_line.save()

        return Response(
            serializers.ProductLineSerializer(product_line).data,
            status=status.HTTP_200_OK
        )
