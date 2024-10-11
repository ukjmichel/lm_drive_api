from django.contrib import admin
from .models import (
    Product,
    Category,
    SubCategory,
    Stock,
    Store,  # Ensure you import the Store model
)


# Define an inline for SubCategory in Product
class SubCategoryInline(admin.TabularInline):
    model = Product.subcategories.through  # Adjusted to the ManyToMany relationship
    extra = 1  # Number of empty forms to display
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


# Define an inline for Stock in Product
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
        "brand",
        "category",  # Display the category
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
    ]

    def crèche_stock(self, obj):
        """Return the stock quantity for the Crêche store."""
        stock = obj.stocks.filter(store__id="CRE71780").first()  # Filter by store name
        return stock.quantity_in_stock if stock else 0

    def villefranche_stock(self, obj):
        """Return the stock quantity for the Villefranche store."""
        stock = obj.stocks.filter(store__id="VIL69400").first()  # Filter by store name
        return stock.quantity_in_stock if stock else 0

    def total_stock(self, obj):
        """Return the total stock quantity across all stores."""
        total = sum(stock.quantity_in_stock for stock in obj.stocks.all())
        return total

    crèche_stock.short_description = "Crêche"  # Set short description for Crêche stock
    villefranche_stock.short_description = (
        "Villefranche"  # Set short description for Villefranche stock
    )
    total_stock.short_description = (
        "Total Stock"  # Set short description for total stock
    )


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
        "store__name",  # Search by store name directly
        "product__product_name",  # Search by product name
        "product__brand",  # Search by brand through product
    )
    list_filter = (
        "store",  # Filter by store
        "product__brand",  # Filter by brand through product
        "product__category",  # Filter by category through product
        "product__subcategories",  # Filter by subcategories through product
    )


@admin.register(Store)  # Register the Store model
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "address",  # Optional: Display address if needed
        "city",  # Optional: Display city if needed
        "postal_code",  # Optional: Display postal code if needed
        "phone_number",  # Optional: Display phone number if needed
    )  # Adjust this as necessary based on your Store model fields
    search_fields = ("name",)  # Allow searching by store name
    ordering = ("name",)  # Order by store name
