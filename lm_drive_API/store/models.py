from django.db import models
from django.forms import ValidationError
from django.utils.timezone import now
from django.db import transaction


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


class Packaging(models.Model):
    class PackagingTypeChoices(models.TextChoices):
        WEIGHT = "weight", "Weight"
        VOLUME = "volume", "Volume"
        LENGTH = "length", "Length"

    packaging_quantity = models.PositiveIntegerField(help_text="Enter the quantity")
    packaging_value = models.CharField(
        max_length=50, help_text='E.g., "280g", "1L", etc.'
    )
    packaging_type = models.CharField(
        max_length=15, choices=PackagingTypeChoices.choices
    )

    class Meta:
        verbose_name_plural = "Packagings"
        constraints = [
            models.UniqueConstraint(
                fields=["packaging_quantity", "packaging_value", "packaging_type"],
                name="unique_packaging",
            )
        ]

    def __str__(self):
        return (
            f"{self.packaging_quantity} {self.packaging_value} ({self.packaging_type})"
        )


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
    image1 = models.ImageField(upload_to="images/", blank=True, null=True)
    image2 = models.ImageField(upload_to="images/", blank=True, null=True)
    image3 = models.ImageField(upload_to="images/", blank=True, null=True)

    # ForeignKey to Packaging (one-to-many relationship)
    packaging = models.ForeignKey(
        Packaging,
        related_name="products",  # This allows reverse access from Packaging to its products
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "Products"

    def get_total_stock(self):
        total_stock = sum(stock.quantity_in_stock for stock in self.stocks.all())
        return total_stock

    def get_stock_details(self):
        stock_details = {}
        for stock in self.stocks.all():
            stock_details[stock.store.name] = stock.quantity_in_stock
        return stock_details

    def __str__(self):
        return self.product_name

    def get_stock_summary(self):
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
    store_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

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
        unique_together = ("store", "product")
        verbose_name_plural = "Stocks"
        indexes = [
            models.Index(fields=["store", "product"]),
        ]

    def __str__(self):
        return f"{self.store.name} - {self.product.product_name}"

    def clean(self):
        if self.quantity_in_stock < 0:
            raise ValidationError("Quantity in stock cannot be negative.")
        if self.expiration_date < now().date():
            raise ValidationError("Expiration date must be in the future.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Calls clean method for validations
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def adjust_stock(self, quantity):
        if quantity < 0:
            raise ValidationError("Quantity to adjust cannot be negative.")
        if quantity > self.quantity_in_stock:
            raise ValidationError(
                f"Not enough stock for {self.product.product_name} in {self.store.name}."
            )
        self.quantity_in_stock -= quantity
        self.save()

    def restock(self, quantity):
        if quantity < 0:
            raise ValidationError("Restocking quantity cannot be negative.")
        self.quantity_in_stock += quantity
        self.save()

    @classmethod
    def handle_payment_success(cls, store_id, product_id, quantity):
        try:
            with transaction.atomic():
                stock = cls.objects.select_for_update().get(
                    store_id=store_id, product_id=product_id
                )
                stock.adjust_stock(quantity)
        except Stock.DoesNotExist:
            raise ValidationError(
                f"Stock not found for store {store_id} and product {product_id}."
            )
        except ValidationError as e:
            raise e
