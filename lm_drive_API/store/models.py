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
    product_id = models.CharField(
        max_length=20, unique=True, primary_key=True
    )  # Unique product identifier as the primary key
    product_name = models.CharField(max_length=100)
    upc = models.CharField(
        max_length=12, unique=True, blank=True
    )  # UPC code for the product
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)  # Quantity in stock
    brand = models.CharField(max_length=100)  # Brand of the product
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT
    )  # ForeignKey to the main Category
    subcategories = models.ManyToManyField(
        SubCategory, related_name="products", blank=True
    )  # Many-to-Many relationship with independent SubCategory
    image = models.ImageField(
        upload_to="images/", blank=True, null=True
    )  # Optional image field

    def __str__(self):
        # Display the product name, brand, and primary category
        return f"{self.product_name} ({self.brand}) - {self.category.name}"
