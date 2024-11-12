from django.db import models
from orders.models import Order


class Payment(models.Model):
    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("requires_action", "Requires Action"),  # For 3D Secure or similar
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments", db_index=True
    )
    payment_method_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="eur")
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.order_id}"
