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


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="brands/logos/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Brands"

    def __str__(self):
        return self.name


class Packaging(models.Model):  # Ensure Packaging is defined before Product
    PACKAGING_TYPE_CHOICES = [
        ("weight", "Weight"),
        ("volume", "Volume"),
        ("length", "Length"),
        # Add more packaging types as needed
    ]

    packaging_quantity = models.PositiveIntegerField(help_text="Enter the quantity")
    packaging_value = models.CharField(
        max_length=50, help_text='E.g., "280g", "1L", etc.'
    )
    packaging_type = models.CharField(max_length=15, choices=PACKAGING_TYPE_CHOICES)

    class Meta:
        verbose_name_plural = "Packagings"
        unique_together = (
            "packaging_quantity",
            "packaging_value",
            "packaging_type",
        )  # Ensure uniqueness

    def __str__(self):
        return f"{self.packaging_quantity} {self.packaging_value} ({self.packaging_type})"  # E.g., "280g (Weight)"


class Product(models.Model):
    product_id = models.CharField(max_length=20, unique=True, primary_key=True)
    product_name = models.CharField(max_length=100)
    upc = models.CharField(max_length=12, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.ForeignKey(
        "Brand", related_name="products", on_delete=models.SET_NULL, null=True
    )
    category = models.ForeignKey(
        "Category", related_name="products", on_delete=models.PROTECT
    )
    subcategories = models.ManyToManyField(
        "SubCategory", related_name="products", blank=True
    )
    image = models.ImageField(upload_to="images/", blank=True, null=True)
    packaging = models.ForeignKey(
        Packaging, related_name="products", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Products"

    def get_total_stock(self):
        total_stock = sum(stock.quantity_in_stock for stock in self.stocks.all())
        return total_stock

    def get_stock_details(self):
        """
        Return a dictionary of stock quantities for this product in each store.
        """
        stock_details = {}
        for stock in self.stocks.all():
            stock_details[stock.store.name] = stock.quantity_in_stock
        return stock_details

    def __str__(self):
        return self.product_name

    def get_stock_summary(self):
        """
        Return a summary including total stock, stock details, and expiration dates.
        """
        stock_summary = {
            "total_stock": self.get_total_stock(),
            "stock_details": {},
        }

        for stock in self.stocks.all():
            stock_summary["stock_details"][stock.store.name] = {
                "quantity_in_stock": stock.quantity_in_stock,
                "expiration_date": stock.expiration_date,
            }

        return stock_summary


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

    class Meta:
        verbose_name_plural = "Stores"

    def __str__(self):
        return self.name


class Stock(models.Model):
    store = models.ForeignKey(Store, related_name="stocks", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="stocks", on_delete=models.CASCADE
    )
    quantity_in_stock = models.PositiveIntegerField(default=0)
    expiration_date = models.DateField()

    class Meta:
        unique_together = ("store", "product")  # Composite unique constraint
        verbose_name_plural = "Stocks"

    def __str__(self):
        return f"{self.store.name} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
