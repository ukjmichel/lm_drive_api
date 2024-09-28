from django.contrib import admin
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id",
        "product_name",
        "upc",
        "price",
        "stock",
        "brand",
        "category",
    )
    search_fields = ("product_id", "product_name", "upc", "brand", "category")
    list_filter = ("category",)
