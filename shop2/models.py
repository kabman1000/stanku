from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.db.models import F, Sum
from django.core.validators import MinValueValidator

class ProductManager(models.Manager):
    def get_queryset(self):
        return super(ProductManager, self).get_queryset().filter(is_active=True)


class Category(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def get_absolute_url(self):
        return reverse('shop2:category_list', args=[self.slug])

    def __str__(self):
        return self.name
    
class SubCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return self.name

    
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null= True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, blank=True, null= True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_author')
    title = models.CharField(max_length=255,unique=True)
    size = models.CharField(max_length=255, null=True)
    author = models.CharField(max_length=255, default='admin')
    code = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='images/', default='images/wall.jpg')
    slug = models.SlugField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    in_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    products = ProductManager()
    inventory = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    can_backorder = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-created',)

    def get_absolute_url(self):
        return reverse('shop2:shop_products_detail', args=[self.slug])

    def __str__(self):
        return self.title

    @property
    def can_order(self):
        if self.has_inventory():
            return True
        elif self.can_backorder:
            return True
        return False
    
    @property
    def order_btn_title(self):
        if self.can_order and not self.has_inventory():
            return "Backorder"
        if not self.can_order:
            return "Cannot purchase."
        return "Purchase"

    def has_inventory(self):
        return self.inventory > 0 # True or False

    def remove_items_from_inventory(self, count=1, save=True):
        current_inv = self.inventory
        current_inv -= count
        self.inventory = current_inv
        if save == True:
            self.save()
        return self.inventory


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_order')
    full_name = models.CharField(max_length=50)
    address1 = models.CharField(max_length=250)
    phone = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    billing_status = models.BooleanField(default=False)
    order_number = models.AutoField(primary_key=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ('-created',)
    
    def __str__(self):
        return str(self.created)

        

class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='item',
                              on_delete=models.SET_NULL,
                              null= True)
    product = models.ForeignKey(Product,
                                related_name='order_items',
                                on_delete=models.SET_NULL,
                                null= True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    inventory = models.PositiveIntegerField(default=0,null=True)

    def __str__(self):
        return str(self.id)
    
    @property
    def total_cost(self):
        return self.quantity * self.price
    
    def save(self, *args, **kwargs):
        if self.product:
            self.inventory = self.product.inventory
        super().save(*args, **kwargs)



class InventoryReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inv_report')
    product_title = models.CharField(max_length=255, blank=True, null=True)
    days_on_hand = models.PositiveIntegerField(default=0)
    inventory_on_hand = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-created',)

    def calculate_days_on_hand(self):
    # Calculate days on hand based on last order date
        if self.product.created:
            days_on_hand = (timezone.now() - self.product.created).days
            return days_on_hand
        return 0

    def calculate_inventory_on_hand(self):
        # Calculate inventory on hand
        return self.product.inventory

    def calculate_amount_sold(self):
        total_quantity_sold = OrderItem.objects.filter(
            product=self.product,
            order__created__date=self.created
        ).aggregate(total=Sum('quantity'))['total']
        return total_quantity_sold if total_quantity_sold else 0

    def save(self, *args, **kwargs):
        self.product_title = self.product.title
        self.days_on_hand = self.calculate_days_on_hand()
        self.inventory_on_hand = self.calculate_inventory_on_hand()
        self.quantity_sold = self.calculate_amount_sold()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_title
    


class SalesReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='report_prod')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    product_title = models.CharField(max_length=255, blank=True, null=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_units_sold = models.PositiveIntegerField(default=0)
    number_of_transactions = models.PositiveIntegerField(default=0)
    average_transaction_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='report', null=True)
    date_created = models.DateTimeField(default=timezone.now)

    def calculate_total_sales(self):
        total_sales = self.product.order_items.filter(order__created__date=self.date_created.date()).aggregate(total=Sum(F('price') * F('quantity')))['total']
        return total_sales if total_sales else Decimal('0.00')

    def calculate_total_units_sold(self):
        total_units_sold = self.product.order_items.filter(order__created__date=self.date_created.date()).aggregate(total=Sum('quantity'))['total']
        return total_units_sold if total_units_sold else 0

    def calculate_number_of_transactions(self):
        number_of_transactions = self.product.order_items.filter(order__created__date=self.date_created.date()).values('order_id').distinct().count()
        return number_of_transactions

    def calculate_average_transaction_value(self):
        if self.number_of_transactions > 0:
            return self.total_sales / Decimal(self.number_of_transactions)
        return Decimal('0.00')
    
    def calculate_product_price(self):
        return self.product.price
    
    def __str__(self):
        return self.product_title

    def save(self, *args, **kwargs):
        self.product_price = self.calculate_product_price()
        self.product_title = self.product.title
        self.total_sales = self.calculate_total_sales()
        self.total_units_sold = self.calculate_total_units_sold()
        self.number_of_transactions = self.calculate_number_of_transactions()
        self.average_transaction_value = self.calculate_average_transaction_value()
        super().save(*args, **kwargs)


