from django.contrib import admin, messages
from .models import Category, Product, SubCategory

from io import BytesIO
from django.http import HttpResponse
try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'inventory', 'code', 'price',
                    'in_stock', 'created', 'updated','subcategory']
    list_filter = ['in_stock', 'is_active']
    list_editable = ['price', 'in_stock']
    prepopulated_fields = {'slug': ('title',), 'code': ('title',)}
    readonly_fields = ['created_by']
    search_fields = ['title', 'code']

    actions = ['export_products_xlsx']

    def get_changeform_initial_data(self, request):
        return {'created_by': request.user.pk}

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def export_products_xlsx(self, request, queryset):
        """
        Export selected products to an .xlsx file with columns:
        code, name, quantity, unit price
        """
        if Workbook is None:
            messages.error(request, "openpyxl is not installed. Run: pip install openpyxl")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        # Header row
        ws.append(['Code', 'Name', 'Quantity', 'Unit Price'])

        # Data rows
        for p in queryset:
            code = getattr(p, 'code', '')
            name = getattr(p, 'title', '')  # Product name stored in title
            quantity = getattr(p, 'inventory', 0)
            price = getattr(p, 'price', None)
            # ensure price is number or empty
            ws.append([code, name, quantity, float(price) if price is not None else ''])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = "products_export.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    export_products_xlsx.short_description = "Export selected products to Excel (.xlsx)"


@admin.register(SubCategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display=['name','categories']

