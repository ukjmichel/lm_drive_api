from django.db import models
from store.models import Product
from django.contrib.auth.models import User
import random
import uuid


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

    order_id = models.CharField(
        max_length=8, unique=True, default=generate_order_id, editable=False
    )  # Unique 8-character UUID
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True
    )  # Allow null temporarily
    address = models.TextField()  # Shipping address
    created_at = models.DateTimeField(auto_now_add=True)  # Order creation date
    updated_at = models.DateTimeField(auto_now=True)  # Last update date
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )  # Total amount for the order
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )  # Order status

    def __str__(self):
        return f"Order ID: {self.order_id}, Customer: {self.customer.username if self.customer else 'Guest'}, Total: {self.total_amount}, Status: {self.status}"

    def calculate_total_amount(self):
        """Calculate the total amount based on order items."""
        total = sum(item.total for item in self.items.all())  # Use total from OrderItem
        return total

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        self.total_amount = self.calculate_total_amount()  # Call calculate_total_amount
        super().save(*args, **kwargs)  # Save the order instance first


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE, to_field="order_id"
    )  # Link to Order
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the product
    quantity = models.PositiveIntegerField(default=1)  # Quantity of the product
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )  # Total price for the item

    class Meta:
        unique_together = (
            "order",
            "product",
        )  # Set order and product as unique together

    def __str__(self):
        return f"Order ID: {self.order.order_id}, Product: {self.product}, Total: {self.total}"

    def calculate_total(self):
        """Calculate the total price for the item."""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        """Override the save method to update total."""
        if self.product:
            self.total = self.calculate_total()
        super().save(*args, **kwargs)  # Save the order item instance first
