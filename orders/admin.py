from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline  # Import TabularInline from unfold
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Min,Sum,F
from .models import Order, OrderItem,InventoryReport,SalesReport,Product, InventoryMovement
from datetime import timedelta, datetime
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from decimal import Decimal
from django.db import models
from unfold.contrib.filters.admin import RangeDateFilter, RangeDateTimeFilter
from django.core.exceptions import ValidationError

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0  # No extra blank forms

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    inlines = [OrderItemInline]  # Add the inline class here
    list_filter_submit = True  # Submit button at the bottom of the filter
    list_filter = (
        ("created", RangeDateFilter),  # Date filter
    )
    search_fields = ['order_number']
    pass



@admin.register(InventoryReport)
class InventoryAdmin(ModelAdmin):
    actions = ["export_as_csv"]
    list_filter_submit = True  # Submit button at the bottom of the filter
    list_filter = (
        ("created", RangeDateFilter),  # Date filter
    )

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

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=100)  # Last 30 days

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
                        'inventory_on_hand': product.inventory,
                        'quantity_sold': 0,
                    }
                )

                if created:
                    reports_to_create.append(report)
                else:
                    # If the report already exists, add it to the list to update
                    report.inventory_on_hand = product.inventory
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

    list_display = ['product_title', 'days_on_hand', 'inventory_on_hand', 'quantity_sold', 'created']
    search_fields = ['product_title']
    list_per_page = 20


@admin.register(SalesReport)
class SalesAdmin(ModelAdmin):
    actions = ["export_as_csv"]
    list_filter_submit = True  # Submit button at the bottom of the filter
    list_filter = (
        ("date_created", RangeDateFilter),  # Date filter
    )

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ["product_title", "id","order"]]

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
        products = Product.objects.all()

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
                ['product_price', 'product_title', 'total_units_sold', 'number_of_transactions', 'average_transaction_value', 'total_sales']
            )

        return SalesReport.objects.filter(date_created__gte=start_date).exclude(date_created__time=datetime.min.time())

    list_display = ['product','product_title', 'product_price', 'total_sales', 'total_units_sold', 'number_of_transactions', 'average_transaction_value', 'date_created']
    list_per_page = 20

class SalesAdmin(ModelAdmin):
    actions = ["export_as_csv"]
    list_filter_submit = True  # Submit button at the bottom of the filter
    list_filter = (
        ("date_created", RangeDateFilter),  # Date filter
    )

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ["product_title", "id","order"]]

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
        products = Product.objects.all()

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
                ['product_price', 'product_title', 'total_units_sold', 'number_of_transactions', 'average_transaction_value', 'total_sales']
            )

        return SalesReport.objects.filter(date_created__gte=start_date).exclude(date_created__time=datetime.min.time())

    list_display = [ 'date_created','product_title', 'product_price','total_units_sold', 'number_of_transactions', 'total_sales',]
    list_per_page = 20



@admin.register(InventoryMovement)
class InventoryMovementAdmin(ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'timestamp', 'note']
    list_filter = ['movement_type', 'timestamp', 'product']
    search_fields = ['product__title', 'note']

    def save_model(self, request, obj, form, change):
        product = obj.product
        if obj.movement_type == 'IN':
            product.inventory += obj.quantity
        elif obj.movement_type == 'OUT':
            if product.inventory - obj.quantity < 0:
                raise ValidationError("Cannot stock out more than available inventory.")
            product.inventory -= obj.quantity
        product.save()
        super().save_model(request, obj, form, change)