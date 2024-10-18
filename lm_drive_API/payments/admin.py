from django.contrib import admin
from .models import Payment


class PaymentAdmin(admin.ModelAdmin):
    # Specify the fields to be displayed in the list view
    list_display = (
        "id",
        "order",
        "payment_method_id",
        "amount",
        "currency",
        "created_at",
    )
    # Specify all fields as read-only
    readonly_fields = ("order", "payment_method_id", "amount", "currency", "created_at")

    # Optionally, you can disable adding and deleting
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


# Register the Payment model with the custom admin class
admin.site.register(Payment, PaymentAdmin)
