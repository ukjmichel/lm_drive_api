from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of empty forms to display for new OrderItems
    readonly_fields = (
        "price_ht",
        "tva",
        "price_ttc",
        "total_ht",
        "total_ttc",
    )  # Read-only calculated fields


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "customer",
        "store",
        "order_date",
        "total_ht",
        "total_ttc",
        "status",
        "update_date",
        "confirmed_date",
        "fulfilled_date",
    )
    list_filter = ("status", "store", "customer", "order_date")
    search_fields = (
        "order_id",
        "customer__user__username",  # Adjust based on your models
        "store__name",  # Adjust if store has a name field
    )
    ordering = ("-order_date",)
    inlines = [OrderItemInline]
    readonly_fields = (
        "total_ht",
        "total_ttc",
        "update_date",
        "confirmed_date",
        "fulfilled_date",
    )  # Read-only calculated fields


class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "price_ht",
        "tva",
        "price_ttc",
        "quantity",
        "total_ht",
        "total_ttc",
    )
    list_filter = ("order", "product")
    search_fields = (
        "order__order_id",
        "product__product_name",
    )  # Adjust based on your models
    readonly_fields = (
        "order",
        "product",
        "price_ht",
        "tva",
        "price_ttc",
        "total_ht",
        "total_ttc",
    )


# Register the models with the admin site
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
