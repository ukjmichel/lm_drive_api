from django.contrib import admin
from .models import Product, Category, SubCategory, Stock, Store, Packaging, Brand


# Inline for SubCategory in Product
class SubCategoryInline(admin.TabularInline):
    model = Product.subcategories.through  # ManyToMany relationship
    extra = 1  # Number of empty forms to display
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


# Inline for Stock in Product
class StockInline(admin.TabularInline):
    model = Stock  # Use the Stock model to display stock information
    extra = 1  # Number of empty forms to display
    fields = (
        "store",  # Ensure store is included in the stock entry
        "quantity_in_stock",
        "expiration_date",
    )
    verbose_name = "Stock Entry"
    verbose_name_plural = "Stock Entries"


# Packaging Inline for Product
class ProductPackagingInline(admin.TabularInline):
    model = Packaging  # Directly reference the Packaging model (ForeignKey)
    extra = 1
    verbose_name = "Packaging Entry"
    verbose_name_plural = "Packaging Entries"


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# SubCategory Admin
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# Brand Admin
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name")  # Display brand ID and name
    search_fields = ("name",)  # Enable search by brand name
    ordering = ("name",)  # Sort by brand name


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id",
        "product_name",
        "price",
        "brand",
        "category",  # Display the category
        "packaging_display",  # Display packaging as quantity x value
        "crèche_stock",  # Stock for Crêche
        "villefranche_stock",  # Stock for Villefranche
        "total_stock",  # Total stock across all stores
    )
    search_fields = ("product_name", "product_id", "brand")
    ordering = ("product_name",)
    list_filter = (
        "brand",  # Filter by brand
        "category",  # Filter by category
        "subcategories",  # Filter by subcategories
    )
    inlines = [
        SubCategoryInline,
        StockInline,
        # Removed PackagingInline, since it's a ForeignKey relationship
    ]

    # Define stock for specific stores
    def crèche_stock(self, obj):
        """Return the stock quantity for the Crêche store."""
        stock = obj.stocks.filter(
            store__store_id="CRE71780"
        ).first()  # Corrected store ID field
        return stock.quantity_in_stock if stock else 0

    def villefranche_stock(self, obj):
        """Return the stock quantity for the Villefranche store."""
        stock = obj.stocks.filter(
            store__store_id="VIL69400"
        ).first()  # Corrected store ID field
        return stock.quantity_in_stock if stock else 0

    def total_stock(self, obj):
        """Return the total stock quantity across all stores."""
        total = sum(stock.quantity_in_stock for stock in obj.stocks.all())
        return total

    def packaging_display(self, obj):
        """Return the packaging formatted as 'quantity x value'."""
        if obj.packaging:  # Check if packaging exists (ForeignKey relation)
            return (
                f"{obj.packaging.packaging_quantity} x {obj.packaging.packaging_value}"
            )
        return "N/A"

    packaging_display.short_description = "Packaging"
    crèche_stock.short_description = "Crêche"
    villefranche_stock.short_description = "Villefranche"
    total_stock.short_description = "Total Stock"


# Stock Admin
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "store",
        "product",
        "quantity_in_stock",
        "expiration_date",
    )
    ordering = ("store",)
    search_fields = (
        "store__name",  # Search by store name
        "product__product_name",  # Search by product name
        "product__brand",  # Search by brand
    )
    list_filter = (
        "store",  # Filter by store
        "product__brand",  # Filter by brand through product
        "product__category",  # Filter by category
        "product__subcategories",  # Filter by subcategories
    )


# Store Admin
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "store_id",
        "name",
        "address",  # Display address if needed
        "city",  # Display city if needed
        "postal_code",  # Display postal code
        "phone_number",  # Display phone number
    )
    search_fields = ("name",)  # Search by store name
    ordering = ("name",)  # Order by store name


# Packaging Admin
@admin.register(Packaging)
class PackagingAdmin(admin.ModelAdmin):
    list_display = ("formatted_packaging",)  # Display formatted packaging
    search_fields = ("packaging_quantity", "packaging_value")
    ordering = ("packaging_quantity",)

    def formatted_packaging(self, obj):
        """Return the packaging formatted as 'quantity x value'."""
        return f"{obj.packaging_quantity} x {obj.packaging_value}"

    formatted_packaging.short_description = "Packaging"
