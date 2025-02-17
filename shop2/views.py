import os
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from shop2.models import Product, Order, OrderItem, InventoryReport, SalesReport
from shop2.basket import Basket
from django.contrib import messages
# for generating pdf invoice
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.generic import View
import sys
# for generating pdf invoice
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


# Create your views here.
def shop_products_all(request):
    products = Product.products.all().filter(in_stock=True)
    return render(request, 'sj/home.html', {'products': products})

def shop_products_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, in_stock=True)
    return render(request, 'sj/products/single.html', {'product': product})

def basket_summary(request):
    basket = Basket(request)
    print(basket.basket)
    return render(request, 'sj/summary.html', {'basket': basket})


def basket_add(request):
    basket = Basket(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('productqty'))
        product = get_object_or_404(Product, id=product_id)
        
        # Check if the inventory is sufficient
        if product.inventory < product_qty:
            response = JsonResponse({'error': f"Insufficient Inventory for {product.title}. Available: {product.inventory}"})
            response.status_code = 400  # Set the status code to 400 (Bad Request)
            return response

        # Add the product to the basket
        basket.add(product=product, qty=product_qty)
        basketqty = basket.__len__()

        response = JsonResponse({'qty': basketqty})
        return response

def payment_confirmation(order_number):
    Order.objects.filter(order_number=order_number).update(billing_status=True)
    print(order_number)


def shopadd(request):
    basket = Basket(request)
    if request.POST.get('action') == 'post':

        order_number = request.POST.get('order_number')
        user_id = request.user.id
        baskettotal = basket.get_total_price()
        full_name = request.POST.get('cusName')
        address1 = request.POST.get('add')
        phone = request.POST.get('phone_num')
        # Check if order exists
        if Order.objects.filter(order_number=order_number).exists():
            pass
        else:
            #print(order_number)
            order = Order.objects.create(user_id=user_id, full_name=full_name, address1=address1, phone=phone,total_paid=baskettotal, order_number=order_number)
            payment_confirmation(order_number)
            order_id = order.pk
            
            for item in basket:
                quant = item['qty']
                pro = item['product']
                print(pro)
                product_id = item['product'].id
                inv = Product.objects.get(id=product_id)
                print(inv)
                print(inv.has_inventory())
                if inv.has_inventory():
                    inv.remove_items_from_inventory(count=quant)
                    OrderItem.objects.create(order_id=order_id, product=item['product'], price=item['price'], quantity=item['qty'])
                    order_date = datetime.now().date()

                    # Retrieve inventory reports for the current product and date
                    inventory_reports = InventoryReport.objects.filter(product=inv, created__date=order_date)

                    if not inventory_reports.exists():
                        # If no inventory reports exist for the current date, create a new one
                        inventory_report = InventoryReport.objects.create(product=inv, created=timezone.now())
                        inventory_reports = [inventory_report]

                    # Update all matching inventory reports
                    for inventory_report in inventory_reports:
                        inventory_report.days_on_hand = inventory_report.calculate_days_on_hand()
                        inventory_report.inventory_on_hand = inv.inventory # Assuming this is the correct field to update
                        inventory_report.quantity_sold = inventory_report.calculate_amount_sold()
                        inventory_report.save()

                    order_date = datetime.now().date()

# Retrieve sales reports for the current product and date
                    sales_reports = SalesReport.objects.filter(product=inv, date_created__date=order_date)

                    if not sales_reports.exists():
                        # If no sales reports exist for the current date, create a new one
                        sales_report = SalesReport.objects.create(product=inv, date_created=timezone.now())
                        sales_reports = [sales_report]

                    # Update all matching sales reports
                    for sales_report in sales_reports:
                        sales_report.total_sales = sales_report.calculate_total_sales()
                        sales_report.total_units_sold = sales_report.calculate_total_units_sold()
                        sales_report.number_of_transactions = sales_report.calculate_number_of_transactions()
                        sales_report.average_transaction_value = sales_report.calculate_average_transaction_value()
                        sales_report.save()
                else:
                    messages.error(request, f'{inv.name} is out of stock')

        response = JsonResponse({'success': 'Return something'})
        return response
    

def ShopBasketView(request):
    basket = Basket(request)
    total = str(basket.get_total_price())
    return render(request, 'sj/pay/home.html', {'total': total})


def orders_placed(request):
    order_db = Order.objects.first()
    basket = Basket(request)
    id = order_db.order_number
    #print(basket.basket)
    basket.clear()
    return render(request, 'sj/order_placed.html', {'id':id})


def fetch_resources(uri, rel):
    path = os.path.join(uri.replace(settings.STATIC_URL, ""))
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


class GenerateInvoice(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            order_db = Order.objects.get(order_number = pk , user = request.user , billing_status= True) 
            print(order_db)    #you can filter using order_id as well
        except:
            return HttpResponse("505 Not Found")
        data = {
            'order_id': order_db.order_number,
            'phone': order_db.phone,
            'date': str(order_db.created),
            'name': order_db.full_name,
            'order': order_db,
            'amount': order_db.total_paid,
        }
        pdf = render_to_pdf('sj/pay/invoice.html', data)
        #return HttpResponse(pdf, content_type='application/pdf')

        # force download
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Invoice_%s.pdf" %(data['order_id'])
            content = "inline; filename='%s'" %(filename)
            #download = request.GET.get("download")
            #if download:
            content = "attachment; filename=%s" %(filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
