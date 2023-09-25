# Generated by Django 4.2.5 on 2023-09-23 22:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0002_alter_productline_variations_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productlinevariation',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='productlinevariation',
            name='product_line',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productline'),
        ),
        migrations.AlterField(
            model_name='productlinevariation',
            name='variation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.variation'),
        ),
        migrations.AlterUniqueTogether(
            name='productlinevariation',
            unique_together={('user', 'variation', 'product_line')},
        ),
    ]