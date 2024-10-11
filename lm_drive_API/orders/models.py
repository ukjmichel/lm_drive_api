from django.db import models
from store.models import Product
import uuid
from authentication.models import Customer
from django.utils import timezone
from django.core.exceptions import ValidationError


def generate_order_id():
    """Generate a unique 4-character UUID."""
    return uuid.uuid4().hex[:4]  # Returns 4 characters from a UUID


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
    order_id = models.CharField(
        max_length=4, default=generate_order_id, unique=True, primary_key=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    confirmed_date = models.DateTimeField(null=True, blank=True)  # Confirmed date
    fulfilled_date = models.DateTimeField(null=True, blank=True)  # Fulfilled date
    update_date = models.DateTimeField(auto_now=True)  # Automatically updated

    def __str__(self):
        return f"Order {self.order_id} for {self.customer}"

    def update_total_amount(self):
        """Update the total amount of the order based on related OrderItems."""
        if self.pk is not None:  # Ensure the instance has a primary key
            total = sum(item.total for item in self.items.all())
            if total != self.total_amount:  # Only update if it has changed
                self.total_amount = total

    def save(self, *args, **kwargs):
        """Override save to manage date fields and calculate total_amount."""
        # Manage confirmed_date
        if self.status == "pending":
            self.confirmed_date = None
        elif self.status == "confirmed" and self.confirmed_date is None:
            self.confirmed_date = timezone.now()

        # Manage fulfilled_date
        if self.status == "fulfilled":
            if self.fulfilled_date is None:
                self.fulfilled_date = timezone.now()
        else:
            self.fulfilled_date = None

        # Save the order first to ensure it has a primary key
        super().save(*args, **kwargs)  # Save first to ensure the order exists

        # Calculate total_amount only if it has related items
        self.update_total_amount()  # Update the total amount based on related OrderItems

        # Save again only if total_amount was updated
        if self.pk is not None and self.total_amount is not None:
            super().save(update_fields=["total_amount", "update_date"])


from django.core.exceptions import ValidationError


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False
    )  # Make the price non-editable
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.order.order_id}|{self.id}"

    def clean(self):
        """Ensure that the quantity is at least 1."""
        if self.quantity < 1:
            raise ValidationError(
                "The quantity must be at least 1. Please provide a valid quantity."
            )

    def save(self, *args, **kwargs):
        """Set the price from the product and calculate total before saving."""
        # Validate the model first (this will call the clean method)
        self.full_clean()

        # Ensure that price is set to the product's price
        if self.product:
            self.price = self.product.price

        # Calculate total based on price and quantity
        self.total = self.price * self.quantity

        super().save(*args, **kwargs)

        # After saving the order item, update the order's total amount
        self.order.update_total_amount()
        # Save the order to ensure the total amount is updated in the database
        self.order.save(update_fields=["total_amount", "update_date"])

    def delete(self, *args, **kwargs):
        """Before deleting the order item, update the order's total amount."""
        # Update the order's total amount first
        self.order.update_total_amount()

        # Call super to delete the item
        super().delete(*args, **kwargs)

        # Ensure the order is saved to update the update_date
        self.order.save(update_fields=["total_amount", "update_date"])
