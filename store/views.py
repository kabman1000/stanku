from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import Category, Product, SubCategory


def product_all(request):
    products = Product.products.all().filter(in_stock=True)
    return render(request, 'store/home.html', {'products': products})

def all_products(request):
    products = Product.products.all().filter(in_stock=True)
    category = Category.objects.values()
    print(category)
    return render(request, 'store/landing.html', {'products': products, 'category':category})

def get_json_category_data(request):
    qs_val = list(Category.objects.values())
    return JsonResponse({'data':qs_val})

def get_json_subcategory_data(request, *args, **kwargs):
    selected_cat = kwargs.get('cat')
    obj_subcat = list(SubCategory.objects.filter(categories__name=selected_cat).values())
    return JsonResponse({'data': obj_subcat})

def category_list(request, category_slug=None):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/products/category.html', {'category': category, 'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, in_stock=True)
    return render(request, 'store/products/single.html', {'product': product})

def searchBar(request):
    if request.method == 'GET':
        query = request.GET.get('query')
        if query:
            products = Product.objects.filter(code__icontains=query)
            return render(request, 'store/searchbar.html', {'products': products})
        else:
            print("No info to show")
            return request(request, 'store/searchbar.html', {})    
        
def get_subcategory(request):
    user_id = request.user.id
    csrf = request.GET.get('csrfmiddlewaretoken')
    print(csrf)
    cat = request.GET.get('cat')
    print(cat)
    subcat = request.GET.get('subcat')
    products = Product.objects.filter(in_stock=True).filter(category__name__contains=cat).filter(subcategory__name__contains=subcat)
    print(products)
    return render(request, 'store/products/subcategory.html', {'products':products})

