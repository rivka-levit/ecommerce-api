# Generated by Django 4.2.5 on 2023-09-21 05:16

from django.db import migrations, models
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_productimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=product.models.product_image_file_path),
        ),
    ]
