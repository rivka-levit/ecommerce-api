"""
Views for product APIs.
"""
from django.db.models import Prefetch

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response


from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes
)

from .models import (Category, Brand, Product, ProductLine, ProductImage,
                     Attribute, Variation, ProductLineVariation)
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


@extend_schema_view(
    list=extend_schema(description='Retrieve the list of all the categories.'),
    create=extend_schema(description='Create a new category. Can be assigned '
                                     'to parent category by indicating its '
                                     '"id" in the field "parent".'),
    retrieve=extend_schema(description='Retrieve a single category.'),
    update=extend_schema(description='Full update of a category. All the '
                                     'fields must be filled.'),
    partial_update=extend_schema(description='Partial update of a category.'),
    destroy=extend_schema(description='Remove a category from the system.')
)
class CategoryViewSet(BaseStoreViewSet):
    """View for managing category APIs."""

    queryset = Category.objects.filter(
        is_active=True
    ).prefetch_related(Prefetch('attributes'))
    serializer_class = serializers.CategorySerializer
    lookup_field = 'slug'


@extend_schema_view(
    list=extend_schema(description='Retrieve the list of all the brands.'),
    create=extend_schema(description='Create a new brand.'),
    retrieve=extend_schema(description='Retrieve a single brand.'),
    update=extend_schema(description='Full update of a brand. All the '
                                     'fields must be filled.'),
    partial_update=extend_schema(description='Partial update of a brand.'),
    destroy=extend_schema(description='Remove a brand from the system.')
)
class BrandViewSet(BaseStoreViewSet):
    """View for managing brand APIs."""
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = serializers.BrandSerializer
    lookup_field = 'slug'


@extend_schema_view(
    list=extend_schema(
        description='List of products. Can be filtered by category or brand. '
                    'Returns also all the sub categories products.',
        parameters=[
            OpenApiParameter(
                'category',
                OpenApiTypes.STR,
                description='Category slug',
                required=False
            ),
            OpenApiParameter(
                'brand',
                OpenApiTypes.STR,
                description='Brand slug',
                required=False
            )
        ]
    )
)
class ProductViewSet(BaseStoreViewSet):
    """View for managing product APIs."""
    queryset = Product.objects.filter(is_active=True).select_related(
        'category', 'brand'
    ).prefetch_related(
        Prefetch('attributes')
    ).prefetch_related(
        Prefetch('product_lines__images')
    ).prefetch_related(
        Prefetch('product_lines__variations__attribute')
    )
    serializer_class = serializers.ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        """Retrieve products, filtering them by category."""
        category_slug = self.request.query_params.get('category')
        brand_slug = self.request.query_params.get('brand')

        queryset = super().get_queryset()

        if category_slug:
            try:
                category = Category.objects.get(
                    user=self.request.user,
                    slug=category_slug
                )
                categories = category.get_descendants(include_self=True)

                queryset = queryset.filter(category__in=categories).distinct()

            except Category.DoesNotExist:
                pass

        if brand_slug:
            queryset = queryset.filter(
                brand__slug=brand_slug
            ).order_by('-id').distinct()

        return queryset


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'product_slug',
                OpenApiTypes.STR,
                description='Filter by product.',
                required=True
            )
        ],
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    destroy=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    attach_variation=extend_schema(
            request=None,
            responses={204: None},
            parameters=[
                OpenApiParameter(
                    'id',
                    OpenApiTypes.INT,
                    OpenApiParameter.PATH,
                    required=True)
            ]
        ),
    detach_variation=extend_schema(
        request=None,
        responses={204: None},
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
)
class ProductLineViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """View for managing product lines."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CreateProductLineSerializer

    def get_queryset(self):
        queryset = ProductLine.objects.filter(
            user=self.request.user
        ).prefetch_related(
            Prefetch('images')
        ).prefetch_related(
            Prefetch('variations__attribute')
        )
        slug = self.request.query_params.get('product_slug', None)

        if slug:
            queryset = queryset.filter(product__slug=slug)

        return queryset.order_by('ordering')

    def get_serializer_class(self):
        """Return the serializer class for a particular request."""

        if self.action == 'list':
            return serializers.ProductLineSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        methods=['POST'],
        detail=True,
        url_path=r'attach-variation/(?P<variation_id>\d+)'
    )
    def attach_variation(self, request, pk=None, variation_id=None):
        """Assign variation to a product line."""

        product_line = self.get_object()
        variation = Variation.objects.get(id=variation_id)

        if variation not in product_line.variations.all():
            ProductLineVariation.objects.create(
                user=request.user,
                product_line=product_line,
                variation=variation
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST'],
        detail=True,
        url_path=r'detach-variation/(?P<variation_id>\d+)'
    )
    def detach_variation(self, request, pk=None, variation_id=None):
        """Detach variation from a product line."""

        try:
            pl_v = ProductLineVariation.objects.get(
                product_line_id=pk,
                variation_id=variation_id
            )
            pl_v.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except ProductLineVariation.DoesNotExist:

            return Response(status=status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'product_line_id',
                OpenApiTypes.INT,
                description='Filter by product_line.',
                required=True
            )
        ],
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    destroy=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
    upload_image=extend_schema(
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                required=True)
        ]
    ),
)
class ProductImageViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """View for managing the images of product lines."""

    serializer_class = serializers.ProductImageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ProductImage.objects.filter(user=self.request.user)
        product_line_id = self.request.query_params.get(
            'product_line_id',
            None
        )

        if product_line_id:
            qs = qs.filter(product_line_id=product_line_id)

        return qs.order_by('ordering')

    def get_serializer_class(self):
        """Return the serializer class for a particular request."""

        if self.action == 'create':
            return serializers.CreateProductImageSerializer
        if self.action == 'upload_image':
            return serializers.UploadImageSerializer
        if any((
                self.action == 'update',
                self.action == 'partial_update'
        )):
            return serializers.UpdateImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Delete image object and remove the image file uploaded to
        the database.
        """

        image_obj = self.get_object()

        if image_obj.image:
            image_obj.image.delete()
        self.perform_destroy(image_obj)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to the image object."""

        image_obj = self.get_object()

        request.data._mutable = True
        request.data['alt_text'] = image_obj.alt_text
        request.data._mutable = False

        serializer = self.get_serializer(image_obj, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        description='List of all the attributes. '
                    'Can be filtered by category or product.',
        parameters=[
            OpenApiParameter(
                'category',
                OpenApiTypes.STR,
                description='Category slug',
                required=False
            ),
            OpenApiParameter(
                'product',
                OpenApiTypes.STR,
                description='Product slug',
                required=False
            )
        ]
    )
)
class AttributeViewSet(BaseStoreViewSet):
    """View set for managing attributes."""

    queryset = Attribute.objects.all()
    serializer_class = serializers.AttributeDetailSerializer

    def get_queryset(self):
        """Filter queryset by category or product."""
        qs = super().get_queryset()
        category_slug = self.request.query_params.get('category', None)
        product_slug = self.request.query_params.get('product', None)

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                qs = qs.filter(categories__in=[category])
            except Category.DoesNotExist:
                pass

        if product_slug:
            try:
                product = Product.objects.get(slug=product_slug)
                qs = qs.filter(products__in=[product])
            except Product.DoesNotExist:
                pass

        return qs

    def get_serializer_class(self):
        """Return a serializer class for different requests."""

        if self.action == 'partial_update':
            return serializers.AttributePatchSerializer
        elif self.action in (
                'variation_create',
                'variation_update',
                'variation_delete'
        ):
            return serializers.CreateUpdateDeleteVariationSerializer

        return self.serializer_class

    @action(methods=['POST'], detail=True, url_path='variation-create')
    def variation_create(self, request, pk=None):
        """Create and return variation of a particular attribute."""

        attribute = self.get_object()

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user, attribute=attribute)

            return Response(serializer.data, status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['PATCH'],
        detail=True,
        url_path=r'variation-update/(?P<variation_id>\d+)'
    )
    def variation_update(self, request, pk=None, variation_id=None):
        """Update variation of a particular attribute."""

        attribute = self.get_object()
        variation = Variation.objects.get(id=variation_id, attribute_id=pk)

        serializer = self.get_serializer(variation, data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user, attribute=attribute)

            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['DELETE'],
        detail=True,
        url_path=r'variation-delete/(?P<variation_id>\d+)'
    )
    def variation_delete(self, request, pk=None, variation_id=None):
        """Remove variation of a particular attribute from database."""

        variation = Variation.objects.get(id=variation_id, attribute_id=pk)
        variation.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
