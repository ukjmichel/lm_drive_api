from django.contrib import admin
from .models import Product, Category, SubCategory


# Define an inline for SubCategory in Product
class SubCategoryInline(admin.TabularInline):
    model = (
        Product.subcategories.through
    )  # Use the through model for the ManyToMany relationship
    extra = 1  # Number of empty forms to display
    fields = ("subcategory",)  # Specify the field to display for editing
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id",
        "product_name",
        "price",
        "stock",
        "brand",
    )  # Use product_id instead of id
    search_fields = ("product_name", "product_id", "brand")
    ordering = ("product_name",)
    inlines = [SubCategoryInline]  # Add inline for SubCategories

    # You can add more customizations here if needed
