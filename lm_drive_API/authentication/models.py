import random
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction


def generate_unique_customer_id():
    """Generate a unique 10-digit customer ID."""
    while True:
        customer_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
        if not Customer.objects.filter(customer_id=customer_id).exists():
            return customer_id


class Customer(models.Model):
    customer_id = models.CharField(
        max_length=10, unique=True, default=generate_unique_customer_id
    )
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)  # Ensure email is unique
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

    def clean(self):
        """Custom validation for the customer_id and other fields."""
        if len(self.customer_id) != 10 or not self.customer_id.isdigit():
            raise ValidationError("Customer ID must be a 10-digit number.")

        if not self.email:
            raise ValidationError("Email cannot be empty.")

        if self.phone and not re.match(r"^\+?1?\d{9,15}$", self.phone):
            raise ValidationError("Phone number must be in a valid format.")

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["last_name", "first_name"]  # Ordering by last and first names

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save to ensure customer ID is unique."""
        self.full_clean()  # This calls clean() automatically
        super().save(*args, **kwargs)
