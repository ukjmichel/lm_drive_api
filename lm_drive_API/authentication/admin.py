from django.contrib import admin
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_id",
        "email",
        "stripe_customer_id",  # Display Stripe customer ID in the admin list
    )
    search_fields = ("email", "customer_id", "stripe_customer_id")
    readonly_fields = ("stripe_customer_id",)  # Set Stripe customer ID as read-only

    def get_queryset(self, request):
        """Override to return only users with active status."""
        qs = super().get_queryset(request)
        return qs


admin.site.register(Customer, CustomerAdmin)
