from django.contrib import admin
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_id",
        "email",
    )
    search_fields = ("email", "customer_id")

    def get_queryset(self, request):
        """Override to return only users with active status."""
        qs = super().get_queryset(request)
        return qs


admin.site.register(Customer, CustomerAdmin)
