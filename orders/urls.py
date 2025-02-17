from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('add/', views.add, name='add'),

    #path('<slug:slug>', views.sale_orders, name='sales'),
    path("statistics/", views.statistics_view, name="shop-statistics"),
    path('sales/', views.sales, name='sales'),
    path('dash/', views.dash, name='dash'),
    path("chart/filter-options/", views.get_filter_options, name="chart-filter-options"),
    #path("chart/filter-options/month/", views.get_filter_options_month, name="chart-filter-options-month"),
    path("chart/sales/<int:year>/", views.get_sales_chart, name="chart-sales"),
    path("chart/most-sold/<int:year>/", views.get_most_sold_chart, name="chart-most-sold"),
    path("chart/least-sold/<int:year>/", views.get_least_sold_chart, name="chart-least-sold"),
    path('customers/', views.customer_rel, name='customer-rel'),
    path("chart/spend-per-customer/<int:year>/", views.spend_per_customer_chart, name="chart-spend-per-customer"),
    #path('generateinvoice/<int:pk>/', views.GenerateInvoice.as_view(), name = 'generateinvoice')
]