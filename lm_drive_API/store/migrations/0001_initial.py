# Generated by Django 5.1.4 on 2024-12-14 21:08

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brands/logos/')),
            ],
            options={
                'verbose_name_plural': 'Brands',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('store_id', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=10, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
            ],
            options={
                'verbose_name_plural': 'Stores',
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Subcategories',
            },
        ),
        migrations.CreateModel(
            name='Packaging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('packaging_quantity', models.PositiveIntegerField(help_text='Enter the quantity')),
                ('packaging_value', models.CharField(help_text='E.g., "280g", "1L", etc.', max_length=50)),
                ('packaging_type', models.CharField(choices=[('weight', 'Weight'), ('volume', 'Volume'), ('length', 'Length')], max_length=15)),
            ],
            options={
                'verbose_name_plural': 'Packagings',
                'constraints': [models.UniqueConstraint(fields=('packaging_quantity', 'packaging_value', 'packaging_type'), name='unique_packaging')],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.CharField(max_length=20, primary_key=True, serialize=False, unique=True)),
                ('product_name', models.CharField(max_length=100)),
                ('upc', models.CharField(blank=True, max_length=12, null=True, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price_ht', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix HT')),
                ('tva', models.DecimalField(decimal_places=2, help_text='Enter the VAT percentage, e.g., 20 for 20%', max_digits=4, verbose_name='TVA (%)')),
                ('price_ttc', models.DecimalField(decimal_places=2, editable=False, max_digits=10, verbose_name='Prix TTC')),
                ('is_for_sale', models.BooleanField(default=True, verbose_name='En vente')),
                ('image1', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('image2', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('image3', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('brand', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='store.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='store.category')),
                ('packaging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.packaging')),
                ('subcategories', models.ManyToManyField(blank=True, related_name='products', to='store.subcategory')),
            ],
            options={
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_in_stock', models.PositiveIntegerField(default=0)),
                ('expiration_date', models.DateField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='store.product')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='store.store')),
            ],
            options={
                'verbose_name_plural': 'Stocks',
                'indexes': [models.Index(fields=['store', 'product'], name='store_stock_store_i_c9ca72_idx')],
                'unique_together': {('store', 'product')},
            },
        ),
    ]