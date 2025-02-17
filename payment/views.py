from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from basket.basket import Basket
from orders.models import OrderItem, Order
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View
import sys
# for generating pdf invoice
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os


# Create your views here.
@login_required
def BasketView(request):
    basket = Basket(request)
    total = str(basket.get_total_price())
    return render(request, 'payment/home.html', {'total': total})


def order_placed(request):
    order_db = Order.objects.first()
    basket = Basket(request)
    id = order_db.order_number
    #print(basket.basket)
    basket.clear()
    return render(request, 'payment/order_placed.html', {'id':id})


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
        pdf = render_to_pdf('payment/invoice.html', data)
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
