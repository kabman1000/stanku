from django.urls import path

from shop2 import views

app_name = 'shop2'

urlpatterns = [
    path('products/', views.shop_products_all, name='shop_products_all'),
    path('<slug:slug>', views.shop_products_detail, name='shop_products_detail'),
    path('basketadd/', views.basket_add, name='basket_add'),
    path('shopsummary/', views.basket_summary, name='basket_summary'),
    path('products/basketo', views.ShopBasketView, name='shop_basket'),
    path('adds/', views.shopadd, name='shop_add'),
    path('orderplaced/', views.orders_placed, name='shop_order_placed'),
    path('shopgenerateinvoice/<int:pk>/', views.GenerateInvoice.as_view(), name='shopgenerateinvoice'),
]