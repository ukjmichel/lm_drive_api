from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of empty forms to display for new OrderItems
    readonly_fields = ("total",)  # Make the total read-only since it is calculated


class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer", "order_date", "total_amount", "status")
    list_filter = ("status", "customer", "order_date")
    search_fields = (
        "order_id",
        "customer__user__username",  # Adjust based on your models
    )
    ordering = ("-order_date",)
    inlines = [OrderItemInline]  # Show OrderItems inline in the Order admin form
    readonly_fields = ("total_amount",)  # Make total_amount read-only


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "price", "quantity", "total")
    list_filter = ("order", "product")
    search_fields = ("order__order_id", "product__name")  # Adjust based on your models
    readonly_fields = ["order", "product", "price", "total"]


# Register the models with the admin site
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
