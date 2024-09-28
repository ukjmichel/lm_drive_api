from django.db import models
from store.models import Product
import uuid
from authentication.models import Customer


def generate_order_id():
    """Generate a unique 8-character UUID."""
    return uuid.uuid4().hex[:8]


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("ready", "Ready"),
        ("fulfilled", "Fulfilled"),
    ]
    customer = models.ForeignKey(
        Customer, to_field="customer_id", on_delete=models.CASCADE
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_id = models.CharField(max_length=8, default=generate_order_id, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Order {self.order_id} for {self.customer}"

    def save(self, *args, **kwargs):
        """Override save to calculate total_amount based on related OrderItems."""
        super().save(*args, **kwargs)  # Save first to ensure order exists
        self.total_amount = sum(
            item.total for item in self.items.all()
        )  # Calculate total amount based on related OrderItems
        super().save(update_fields=["total_amount"])  # Save total_amount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"Order ID: {self.order.order_id}, Product: {self.product}, Total: {self.total}"

    def save(self, *args, **kwargs):
        # Calculate total based on price and quantity before saving
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)
