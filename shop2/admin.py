from django.contrib import admin
from shop2.models import Category, SubCategory,Order, OrderItem,InventoryReport,SalesReport,Product
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Min,Sum,F
from datetime import timedelta, datetime
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from decimal import Decimal
from django.db import models

admin.site.register(Order)
admin.site.register(OrderItem)

@admin.site.unregister(InventoryReport)
class InventoryAdmin(admin.ModelAdmin):
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ["product", "id"]]

        earliest_date = queryset.order_by('created').values_list('created', flat=True).first()
        latest_date = queryset.order_by('-created').values_list('created', flat=True).first()

        if earliest_date and latest_date:
            formatted_earliest_date = earliest_date.strftime('%Y-%m-%d')
            formatted_latest_date = latest_date.strftime('%Y-%m-%d')
            date_range = f"{formatted_earliest_date} to {formatted_latest_date}"
            formatted_date = formatted_latest_date  # Use the latest date for the filename
        else:
            # Fallback to the current date if no date is found
            formatted_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"Date: {formatted_date}"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=inventory_{formatted_date}.csv'

        writer = csv.writer(response)

        # Write the date range at the top of the CSV file
        writer.writerow([f"Inventory Report for: {date_range}"])
        writer.writerow([])  # Add an empty row for spacing
        writer.writerow(field_names)  # Write the header row

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export Selected"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        products = Product.objects.all()
        print(products)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        # Collect reports to be created or updated in bulk
        reports_to_create = []
        reports_to_update = []

        for product in products:
            current_date = start_date
            while current_date <= end_date:
                created_datetime = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))

                # Ensure we exclude orders created exactly at midnight
                if created_datetime.time() == datetime.min.time():
                    current_date += timedelta(days=1)
                    continue

                report, created = InventoryReport.objects.get_or_create(
                    product=product,
                    created=created_datetime,
                    defaults={
                        'days_on_hand': 0,
                        'inventory_on_hand': 0,
                        'quantity_sold': 0,
                    }
                )

                if created:
                    reports_to_create.append(report)
                else:
                    # If the report already exists, add it to the list to update
                    reports_to_update.append(report)

                current_date += timedelta(days=1)

        # Bulk create reports
        InventoryReport.objects.bulk_create(reports_to_create, ignore_conflicts=True)

        # Bulk update reports if needed
        if reports_to_update:
            InventoryReport.objects.bulk_update(
                reports_to_update,
                ['days_on_hand', 'inventory_on_hand', 'quantity_sold']
            )

        return InventoryReport.objects.filter(created__gte=start_date).exclude(created__time=datetime.min.time())

    list_filter = (('created', DateRangeFilter), ('created', DateTimeRangeFilter))
    list_display = ['product_title', 'days_on_hand', 'inventory_on_hand', 'quantity_sold', 'created']
    list_per_page = 20


@admin.site.unregister(SalesReport)
class SalesAdmin(admin.ModelAdmin):
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ["product_title", "id"]]

        earliest_date = queryset.order_by('date_created').values_list('date_created', flat=True).first()
        latest_date = queryset.order_by('-date_created').values_list('date_created', flat=True).first()

        if earliest_date and latest_date:
            formatted_earliest_date = earliest_date.strftime('%Y-%m-%d')
            formatted_latest_date = latest_date.strftime('%Y-%m-%d')
            date_range = f"{formatted_earliest_date} to {formatted_latest_date}"
            formatted_date = formatted_latest_date  # Use the latest date for the filename
        else:
            # Fallback to the current date if no date is found
            formatted_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"Date: {formatted_date}"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=sales_{formatted_date}.csv'

        writer = csv.writer(response)

        # Write the date range at the top of the CSV file
        writer.writerow([f"Sales Report for: {date_range}"])
        writer.writerow([])  # Add an empty row for spacing
        writer.writerow(field_names)  # Write the header row

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export Selected"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        products = Product.objects.all()[:2]

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        # Collect reports to be created or updated in bulk
        reports_to_create = []
        reports_to_update = []

        for product in products:
            current_date = start_date
            while current_date <= end_date:
                created_datetime = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))

                # Ensure we exclude records created exactly at midnight
                if created_datetime.time() == datetime.min.time():
                    current_date += timedelta(days=1)
                    continue

                report, created = SalesReport.objects.get_or_create(
                    product=product,
                    date_created=created_datetime,
                    defaults={
                        'product_price': product.price,
                        'product_title': product.title,
                        'total_sales': 0,
                        'total_units_sold': 0,
                        'number_of_transactions': 0,
                        'average_transaction_value': 0,
                    }
                )

                if created:
                    reports_to_create.append(report)
                else:
                    # If the report already exists, update the fields
                    report.product_price = product.price
                    report.product_title = product.title
                    report.total_sales = report.calculate_total_sales()
                    report.total_units_sold = report.calculate_total_units_sold()
                    report.number_of_transactions = report.calculate_number_of_transactions()
                    report.average_transaction_value = report.calculate_average_transaction_value()
                    reports_to_update.append(report)

                current_date += timedelta(days=1)

        # Bulk create reports
        SalesReport.objects.bulk_create(reports_to_create, ignore_conflicts=True)

        # Bulk update reports if needed
        if reports_to_update:
            SalesReport.objects.bulk_update(
                reports_to_update,
                ['product_price', 'product_title', 'total_sales', 'total_units_sold', 'number_of_transactions', 'average_transaction_value']
            )

        return SalesReport.objects.filter(date_created__gte=start_date).exclude(date_created__time=datetime.min.time())

    list_filter = (('date_created', DateRangeFilter), ('date_created', DateTimeRangeFilter))
    list_display = ['product','product_title', 'product_price', 'total_sales', 'total_units_sold', 'number_of_transactions', 'average_transaction_value', 'date_created']
    list_per_page = 20



@admin.site.unregister(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    


@admin.site.unregister(Product)
class ProductAdmin(admin.ModelAdmin):
    

    list_display = ['title', 'inventory', 'code', 'price',
                    'in_stock', 'created', 'updated','subcategory']
    list_filter = ['in_stock', 'is_active']
    list_editable = ['price', 'in_stock']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['code']

@admin.site.unregister(SubCategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display=['name','categories']

