from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem

    extra = 1  # Number of empty forms to display


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]  # Display order items inline
    list_display = [
        "order_id",
        "customer",
        "status",
        "total_amount",
        "created_at",
    ]  # Fields to display in list view
    search_fields = [
        "order_id",
        "customer__username",
    ]  # Allow searching by order ID and customer username


admin.site.register(Order, OrderAdmin)
