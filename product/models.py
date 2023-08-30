from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """Category object."""
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Brand object."""
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product object."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
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
        on_delete=models.SET_NULL)
    is_digital = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
