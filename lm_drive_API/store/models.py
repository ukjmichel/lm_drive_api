from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.CharField(max_length=20, unique=True, primary_key=True)
    product_name = models.CharField(max_length=100)
    upc = models.CharField(max_length=12, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(
        "Category", related_name="products", on_delete=models.PROTECT
    )
    subcategories = models.ManyToManyField(
        "SubCategory", related_name="products", blank=True
    )
    image = models.ImageField(upload_to="images/", blank=True, null=True)

    def get_total_stock(self):
        total_stock = sum(stock.quantity_in_stock for stock in self.stocks.all())
        return total_stock

    def __str__(self):
        return self.product_name


class Store(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # Manually defined ID
    name = models.CharField(max_length=50, unique=True)  # Store name
    address = models.CharField(
        max_length=255, blank=True, null=True
    )  # Address field (optional)
    city = models.CharField(
        max_length=100, blank=True, null=True
    )  # City field (optional)
    postal_code = models.CharField(
        max_length=10, blank=True, null=True
    )  # Postal code field (optional)
    phone_number = models.CharField(
        max_length=15, blank=True, null=True
    )  # Phone number field (optional)

    def __str__(self):
        return self.name


class Stock(models.Model):
    store = models.ForeignKey(
        Store, related_name="stocks", on_delete=models.CASCADE
    )  # Changed from name to store
    product = models.ForeignKey(
        Product, related_name="stocks", on_delete=models.CASCADE
    )
    quantity_in_stock = models.PositiveIntegerField(default=0)
    expiration_date = models.DateField()

    class Meta:
        unique_together = ("store", "product")  # Composite unique constraint

    def __str__(self):
        return f"{self.store} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
