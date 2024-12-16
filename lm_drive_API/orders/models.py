from django.db import models
from store.models import Product
import uuid
from authentication.models import Customer
from django.utils import timezone
from django.db.models import Sum, F
from rest_framework.exceptions import ValidationError as DRFValidationError


def generate_order_id():
    """Generate a unique 8-character UUID."""
    return uuid.uuid4().hex[:8]  # Increased to 8 characters for better uniqueness


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
    total_ht = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total HT"
    )
    total_ttc = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total TTC"
    )
    order_id = models.CharField(
        max_length=8, default=generate_order_id, unique=True, primary_key=True
    )
    store = models.ForeignKey("store.Store", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    confirmed_date = models.DateTimeField(null=True, blank=True)
    fulfilled_date = models.DateTimeField(null=True, blank=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} for {self.customer}"

    def update_totals(self):
        """Update the total HT and total TTC of the order based on related OrderItems."""
        totals = self.items.aggregate(
            total_ht=Sum(F("price_ht") * F("quantity")),
            total_ttc=Sum(F("price_ttc") * F("quantity")),
        )
        self.total_ht = totals["total_ht"] or 0.00
        self.total_ttc = totals["total_ttc"] or 0.00
        # Save only if called explicitly, not within itself

        super(Order, self).save(update_fields=["total_ht", "total_ttc", "update_date"])

    def save(self, *args, **kwargs):
        """Override save to manage date fields and calculate totals."""
        # Manage confirmed_date
        if self.status == "pending":
            self.confirmed_date = None
        elif self.status == "confirmed" and self.confirmed_date is None:
            self.confirmed_date = timezone.now()

        # Manage fulfilled_date
        if self.status == "fulfilled" and self.fulfilled_date is None:
            self.fulfilled_date = timezone.now()
        elif self.status != "fulfilled":
            self.fulfilled_date = None

        super().save(*args, **kwargs)  # Save first to ensure the order exists
        self.update_totals()  # Ensure totals are calculated


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    price_ht = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, verbose_name="Prix HT"
    )
    tva = models.DecimalField(
        max_digits=4, decimal_places=2, editable=False, verbose_name="TVA (%)"
    )
    price_ttc = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, verbose_name="Prix TTC"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    total_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        verbose_name="Total HT",
    )
    total_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        verbose_name="Total TTC",
    )

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return (
            f"Order {self.order.order_id} | "
            f"Product {self.product.product_id} | "
            f"Quantity {self.quantity}"
        )

    def clean(self):
        """Ensure that the quantity is at least 1."""
        if self.quantity < 1:
            raise DRFValidationError("The quantity must be at least 1.")

    def save(self, *args, **kwargs):
        """Set the price and totals before saving."""
        self.full_clean()  # Validate the model

        if self.product:
            # Use product's price_ht and tva
            self.price_ht = self.product.price_ht
            self.tva = self.product.tva
            self.price_ttc = round(self.price_ht * (1 + self.tva / 100), 2)

        # Calculate totals based on quantity
        self.total_ht = round(self.price_ht * self.quantity, 2)
        self.total_ttc = round(self.price_ttc * self.quantity, 2)

        super().save(*args, **kwargs)

        # Update the order's totals
        self.order.update_totals()

    def delete(self, *args, **kwargs):
        """Update the order's totals before deleting."""
        super().delete(*args, **kwargs)
        self.order.update_totals()
