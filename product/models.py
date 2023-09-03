from django.db import models

from mptt.models import MPTTModel, TreeForeignKey

from user.models import User


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
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='brands')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product object."""
    name = models.CharField(max_length=255)
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

    def __str__(self):
        return self.name
