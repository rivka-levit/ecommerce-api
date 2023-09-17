from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from mptt.models import MPTTModel, TreeForeignKey

from user.models import User

from product.fields import OrderField

from datetime import datetime


class Category(MPTTModel):
    """Category object."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='categories')
    is_active = models.BooleanField(default=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Brand object."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='brands')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product object."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='products'
    )
    brand = models.ForeignKey(
        to=Brand,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='products'
    )
    category = TreeForeignKey(
        to=Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products'
    )
    is_digital = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            string = f'{self.name} {datetime.now().timestamp()}'
            self.slug = slugify(string)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductLine(models.Model):
    """Product line object."""
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    ordering = OrderField(to_field='product', blank=True, null=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    sku = models.CharField(max_length=255)
    stock_qty = models.IntegerField()
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name='product_lines'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'product line'
        verbose_name_plural = 'product lines'

    def __str__(self):
        return self.sku

    def clean(self):
        """Check if the ordering number passed on creating product line is
        unique for related product."""

        qs = ProductLine.objects.filter(
            product=self.product
        ).exclude(pk=self.pk)

        for obj in qs:
            if self.ordering == obj.ordering:
                raise ValidationError(
                    'The ordering number of a product line must be unique '
                    'for this particular product.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(ProductLine, self).save(*args, **kwargs)
