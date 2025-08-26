from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from store.models import Product
from django.views.decorators.csrf import csrf_exempt
import json

from .basket import Basket


def basket_summary(request):
    basket = Basket(request)
    print(basket.basket)
    return render(request, 'basket/summary.html', {'basket': basket})


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


def basket_delete(request):
    basket = Basket(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productid'))
        basket.delete(product=product_id)

        basketqty = basket.__len__()
        baskettotal = basket.get_total_price()
        response = JsonResponse({'qty': basketqty, 'subtotal': baskettotal})
        return response


def basket_update(request):
    basket = Basket(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('productqty'))
        print(product_id)
        print(product_qty)
        basket.update(product=product_id, qty=product_qty)

        basketqty = basket.__len__()
        baskettotal = basket.get_total_price()
        response = JsonResponse({'qty': basketqty, 'subtotal': baskettotal})
        return response

@csrf_exempt
def check_inventory(request):
    if request.method == "POST":
        try:
            items = json.loads(request.POST.get("items", "[]"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid data."})

        for item in items:
            product_id = item.get("productid")
            product_qty = int(item.get("productqty", 0))
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({"status": "error", "message": f"Product {product_id} not found."})

            if product_qty > product.inventory:  # Adjust field name if needed
                return JsonResponse({
                    "status": "error",
                    "message": f"Only {product.inventory} units of '{product.title}' available in stock."
                })

        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error", "message": "Invalid request."})