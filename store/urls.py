from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_all, name='product_all'),
    path('<slug:slug>', views.product_detail, name='product_detail'),
    path('shop/<slug:category_slug>/', views.category_list, name='category_list'),
    path('search/', views.searchBar, name='search'),
    path('category-json/', views.get_json_category_data, name='category-json'),
    path('subcategory-json/<str:cat>/', views.get_json_subcategory_data, name='subcategory-json'),
    path('subcategory/', views.get_subcategory, name='subcategory'),
]