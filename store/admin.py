from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Category, Product, SubCategory




@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['title', 'inventory', 'code', 'price',
                    'in_stock', 'created', 'updated','subcategory']
    list_filter = ['in_stock', 'is_active']
    list_editable = ['price', 'in_stock']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['code']


@admin.register(SubCategory)
class SubcategoryAdmin(ModelAdmin):
    list_display=['name','categories']

