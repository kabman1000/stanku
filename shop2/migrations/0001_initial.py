# Generated by Django 4.1.6 on 2024-07-01 08:03

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0006_alter_product_title'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('full_name', models.CharField(max_length=50)),
                ('address1', models.CharField(max_length=250)),
                ('phone', models.CharField(max_length=100)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('total_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('billing_status', models.BooleanField(default=False)),
                ('order_number', models.AutoField(primary_key=True, serialize=False)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_order', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('categories', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop2.category')),
            ],
            options={
                'verbose_name_plural': 'Subcategories',
            },
        ),
        migrations.CreateModel(
            name='SalesReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('product_title', models.CharField(blank=True, max_length=255, null=True)),
                ('total_sales', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_units_sold', models.PositiveIntegerField(default=0)),
                ('number_of_transactions', models.PositiveIntegerField(default=0)),
                ('average_transaction_value', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='report', to='shop2.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_prod', to='store.product')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('size', models.CharField(max_length=255, null=True)),
                ('author', models.CharField(default='admin', max_length=255)),
                ('code', models.CharField(default='', max_length=255)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(default='images/wall.jpg', upload_to='images/')),
                ('slug', models.SlugField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('in_stock', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('inventory', models.PositiveIntegerField(default=0)),
                ('featured', models.BooleanField(default=False)),
                ('can_backorder', models.BooleanField(default=False)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop2.category')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_author', to=settings.AUTH_USER_MODEL)),
                ('subcategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop2.subcategory')),
            ],
            options={
                'verbose_name_plural': 'Products',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('inventory', models.PositiveIntegerField(default=0, null=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='item', to='shop2.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_item', to='store.product')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_title', models.CharField(blank=True, max_length=255, null=True)),
                ('days_on_hand', models.PositiveIntegerField(default=0)),
                ('inventory_on_hand', models.PositiveIntegerField(default=0)),
                ('quantity_sold', models.PositiveIntegerField(default=0)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inv_report', to='store.product')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
