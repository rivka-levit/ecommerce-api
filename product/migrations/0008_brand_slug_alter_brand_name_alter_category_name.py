# Generated by Django 4.2.5 on 2023-10-01 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_category_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='brand',
            name='name',
            field=models.CharField(max_length=210),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=210),
        ),
    ]
