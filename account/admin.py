from django.contrib import admin
from django.db.models import Sum
from django.db.models.functions import TruncMonth, ExtractYear
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

from orders.models import SalesReport
from .models import UserBase


class DashboardAdminSite(admin.AdminSite):
    index_template = "admin/index.html"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        years = sorted(
            set(
                SalesReport.objects.annotate(year=ExtractYear('date_created')).values_list('year', flat=True)
            ),
            reverse=True,
        ) or [now().year]

        current_year = now().year
        all_year_data = {}

        for year in years:
            if year == current_year:
                first_month = now().date().replace(day=1)
                month_labels = [
                    (first_month - relativedelta(months=i)).strftime('%b %Y')
                    for i in range(11, -1, -1)
                ]
            else:
                year_start = now().replace(year=year, month=1, day=1).date()
                month_labels = [
                    year_start.replace(month=month).strftime('%b %Y')
                    for month in range(1, 13)
                ]

            monthly_sales = (
                SalesReport.objects.filter(date_created__year=year)
                .annotate(month=TruncMonth('date_created'))
                .values('month')
                .annotate(total=Sum('total_sales'))
                .order_by('month')
            )
            sales_dict = {
                entry['month'].strftime('%b %Y'): float(entry['total'])
                for entry in monthly_sales
                if entry['month'] is not None
            }
            month_values = [sales_dict.get(label, 0.0) for label in month_labels]

            top_products = (
                SalesReport.objects.filter(date_created__year=year)
                .values('product_title')
                .annotate(units=Sum('total_units_sold'))
                .order_by('-units')[:15]
            )

            all_year_data[str(year)] = {
                'months': month_labels,
                'sales': month_values,
                'product_names': [entry['product_title'] for entry in top_products],
                'units_sold': [entry['units'] for entry in top_products],
            }

        extra_context.update({
            'years': years,
            'selected_year': current_year,
            'dashboard_data': all_year_data,
            'recent_sales_reports': SalesReport.objects.order_by('-date_created')[:10],
        })

        return super().index(request, extra_context)


admin.site.__class__ = DashboardAdminSite
admin.site.register(UserBase)
