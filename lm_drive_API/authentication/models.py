import random
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
    email = models.EmailField(unique=True)  # Ensure email is unique

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.customer_id})"

    def clean(self):
        """Custom validation for the customer ID and email fields."""
        # Validate email
        if not self.email:
            raise ValidationError("Email cannot be empty.")

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save to ensure customer ID is unique and perform validation."""
        self.full_clean()  # This calls clean() automatically
        super().save(*args, **kwargs)
