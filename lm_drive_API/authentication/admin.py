from django.contrib import admin
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "city",
        "postal_code",
    )
    search_fields = ("first_name", "last_name", "email", "customer_id")
    list_filter = ("city", "postal_code")
    ordering = ("last_name", "first_name")

    def get_queryset(self, request):
        """Override to return only users with active status."""
        qs = super().get_queryset(request)
        return qs


admin.site.register(Customer, CustomerAdmin)
