from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View
import sys
from django.contrib import messages
# for generating pdf invoice
from django.utils import timezone
from datetime import datetime
from django.shortcuts import get_object_or_404
from .forms import StockHistorySearchForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum, Avg
from django.db.models.functions import ExtractYear, ExtractMonth
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from .models import Order, Product
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import datetime, timedelta
from collections import OrderedDict
from django.db import transaction, IntegrityError
from basket.basket import Basket
from store.models import Product
from .models import Order, OrderItem, InventoryReport, SalesReport, InventoryMovement
from utils.charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict


def payment_confirmation(order_number):
    Order.objects.filter(order_number=order_number).update(billing_status=True)
    print(order_number)


@transaction.atomic
def add(request):
    basket = Basket(request)
    if request.POST.get('action') != 'post':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    savepoint = transaction.savepoint()

    try:
        order_number = request.POST.get('order_number')
        user_id = request.user.id
        baskettotal = basket.get_total_price()
        full_name = request.POST.get('cusName')
        address1 = request.POST.get('add')
        phone = request.POST.get('phone_num')

        if Order.objects.filter(order_number=order_number).exists():
            return JsonResponse({'error': 'Order already exists'}, status=409)

        # Create Order
        order = Order.objects.create(
            user_id=user_id,
            full_name=full_name,
            address1=address1,
            phone=phone,
            total_paid=baskettotal,
            order_number=order_number
        )
        order_id = order.pk

        payment_confirmation(order_number)

        for item in basket:
            quant = item['qty']
            product = item['product']
            price = item['price']

            inv = Product.objects.select_for_update().get(id=product.id)

            if not inv.has_inventory():
                raise ValueError(f'{inv.name} is out of stock.')

            # Deduct from inventory
            inv.remove_items_from_inventory(count=quant)

            # Create Order Item
            OrderItem.objects.create(
                order_id=order_id,
                product=product,
                price=price,
                quantity=quant
            )

            # Log inventory movement
            InventoryMovement.objects.create(
                product=inv,
                movement_type='OUT',
                quantity=quant,
                note=f"Order #{order_number} stock out"
            )

            # Ensure inventory report exists and update
            today = timezone.now().date()
            inventory_report, _ = InventoryReport.objects.get_or_create(
                product=inv,
                created__date=today,
                defaults={'created': timezone.now()}
            )
            inventory_report.days_on_hand = inventory_report.calculate_days_on_hand()
            inventory_report.inventory_on_hand = inv.inventory
            inventory_report.quantity_sold = inventory_report.calculate_amount_sold()
            inventory_report.save()

            # Ensure sales report exists and update
            sales_report, _ = SalesReport.objects.get_or_create(
                product=inv,
                date_created__date=today,
                defaults={'date_created': timezone.now()}
            )
            sales_report.total_sales = sales_report.calculate_total_sales()
            sales_report.total_units_sold = sales_report.calculate_total_units_sold()
            sales_report.number_of_transactions = sales_report.calculate_number_of_transactions()
            sales_report.average_transaction_value = sales_report.calculate_average_transaction_value()
            sales_report.save()

        transaction.savepoint_commit(savepoint)
        return JsonResponse({'success': 'Order created'})

    except Exception as e:
        transaction.savepoint_rollback(savepoint)
        print(f"Order creation failed: {e}", file=sys.stderr)
        return JsonResponse({'error': 'Failed to process order'}, status=500)


def user_orders(request):
    user_id = request.user.id
    orders = Order.objects.filter(user_id=user_id).filter(billing_status=True)
    print(orders)
    return orders

@login_required
def sales(request):
    user_id = request.user.id
    sales = Order.objects.filter(user_id=user_id).filter(billing_status=True)[:85]
    form = StockHistorySearchForm(request.POST or None)
    total = sum([sale.total_paid for sale in sales])
    print(total)
    if request.method == 'POST':
        sales = Order.objects.filter(user_id=user_id).filter(billing_status=True).filter(created__range=[form['start_date'].value(),form['end_date'].value()])
        total = sum([sale.total_paid for sale in sales])
    return render(request,
                  'account/user/sales.html', {'sales':sales, 'form':form, 'total':total})

def dash(request):
    orders = Order.objects.all()
    order_items = OrderItem.objects.all()
    print(orders)
    print(order_items)
    return render(request,
                  'account/user/dashmoard.html', {'order_items':order_items, 'orders':orders})

def customer_rel(request):
    orders = Order.objects.exclude(full_name="").exclude(phone="").exclude(full_name="cust").annotate(full_name_count=Count('full_name')).filter(full_name_count=1)
    print(orders)
    return render(request,
                  'account/user/customers.html', {'orders':orders})


def get_filter_options(request):
    grouped_purchases = Order.objects.annotate(year=ExtractYear("created")).values("year").order_by("-year").distinct()
    options = [purchase["year"] for purchase in grouped_purchases]

    return JsonResponse({
        "options": options,
    })

def get_sales_chart(request, year):
    purchases = Order.objects.filter(created__year=year)
    grouped_purchases = purchases.annotate(price=F("total_paid")).annotate(month=ExtractMonth("created"))\
        .values("month").annotate(average=Sum("total_paid")).values("month", "average").order_by("month")
        
    sales_dict = get_year_dict()

    for group in grouped_purchases:
        sales_dict[months[group["month"]-1]] = round(group["average"], 2)

    fixed_value = 800000

    return JsonResponse({
        "title": f"Sales in {year}",
        "data": {
            "labels": list(sales_dict.keys()),
            "datasets": [{
                "label": "Amount Sold(₵)",
                "backgroundColor": colorPrimary,
                "borderColor": colorPrimary,
                "data": list(sales_dict.values()),
            },
            {
                "label": "Cost of Goods(₵)",
                "backgroundColor": "#df4e73",
                "borderColor": "#df4e73",
                "data": [fixed_value] * len(sales_dict),
            }
            ]
        },
    })


def spend_per_customer_chart(request, year):
    purchases = Order.objects.filter(created__year=year)
    grouped_purchases = purchases.annotate(price=F("total_paid")).annotate(month=ExtractMonth("created"))\
        .values("month").annotate(average=Avg("total_paid")).values("month", "average").order_by("month")

    spend_per_customer_dict = get_year_dict()

    for group in grouped_purchases:
        spend_per_customer_dict[months[group["month"]-1]] = round(group["average"], 2)

    return JsonResponse({
        "title": f"Spend per customer in {year}",
        "data": {
            "labels": list(spend_per_customer_dict.keys()),
            "datasets": [{
                "label": "Amount ($)",
                "backgroundColor": "#4e73df",
                "borderColor": "#4e73df",
                "data": list(spend_per_customer_dict.values()),
            }]
        },
    })


def statistics_view(request):
    return render(request, "account/user/statistics.html", {})

def get_most_sold_chart(request, year):
    # Query to get the most sold items for the specified year
    most_sold_items = OrderItem.objects.filter(order__created__year=year) \
        .values('product__title').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:75]
    print(most_sold_items)

    # Prepare data for the chart
    labels = [item['product__title'] for item in most_sold_items]
    quantities = [item['total_quantity'] for item in most_sold_items]

    # Prepare JSON response
    response_data = {
        "title": f"Most Sold Items in {year}",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Quantity Sold",
                "backgroundColor": "#4e73df",
                "borderColor": "#4e73df",
                "data": quantities,
            }]
        }
    }

    return JsonResponse(response_data)

def get_least_sold_chart(request, year):
    # Query to get the most sold items for the specified year
    most_sold_items = OrderItem.objects.filter(order__created__year=year) \
        .values('product__title').annotate(total_quantity=Sum('quantity')).order_by('total_quantity')[:10]
    print(most_sold_items)

    # Prepare data for the chart
    labels = [item['product__title'] for item in most_sold_items]
    quantities = [item['total_quantity'] for item in most_sold_items]

    # Prepare JSON response
    response_data = {
        "title": f"Most Sold Items in {year}",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Quantity Sold",
                "backgroundColor": "#4e73df",
                "borderColor": "#4e73df",
                "data": quantities,
            }]
        }
    }

    return JsonResponse(response_data)


def dashboard_callback(request, context):
    context['recent_sales_reports'] = SalesReport.objects.order_by('-date_created')[:10]

    # Get last 12 months as month labels
    today = now().date().replace(day=1)
    months = [today - relativedelta(months=i) for i in range(11, -1, -1)]
    month_labels = [m.strftime('%b %Y') for m in months]
    context['months'] = month_labels

    # Query and build a mapping of month -> sales
    monthly_sales = (
        SalesReport.objects
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(total=Sum('total_sales'))
        .order_by('month')
    )
    sales_dict = {entry['month'].strftime('%b %Y'): float(entry['total']) for entry in monthly_sales}
    context['sales'] = [sales_dict.get(label, 0.0) for label in month_labels]

    # Top 15 Best-Selling Products
    top_products = (
        SalesReport.objects
        .values('product__title')
        .annotate(units=Sum('total_units_sold'))
        .order_by('-units')[:15]
    )
    context['product_names'] = [entry['product__title'] for entry in top_products]
    context['units_sold'] = [entry['units'] for entry in top_products]

    return context