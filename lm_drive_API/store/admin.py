from django import forms
from django.contrib import admin
from .models import Product, Category, SubCategory, Stock, Store, Packaging, Brand
from django.utils.html import mark_safe


# Inline for SubCategory in Product
class SubCategoryInline(admin.TabularInline):
    model = Product.subcategories.through  # ManyToMany relationship
    extra = 1  # Number of empty forms to display
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


# Inline for Stock in Product
class StockInline(admin.TabularInline):
    model = Stock  # Use the Stock model to display stock information
    extra = 0  # Do not display empty forms by default
    fields = (
        "store",  # Ensure store is included in the stock entry
        "quantity_in_stock",
        "expiration_date",
    )
    verbose_name = "Stock Entry"
    verbose_name_plural = "Stock Entries"

    def save_formset(self, request, form, formset, change):
        """
        Custom save logic for the Stock inline.
        """
        if formset.model == Stock:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk and not instance.quantity_in_stock:
                    # Skip saving new stock entries with no quantity
                    continue
                instance.save()
            # Handle deletions
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()


# Packaging Inline for Product
class ProductPackagingInline(admin.TabularInline):
    model = Packaging  # Directly reference the Packaging model (ForeignKey)
    extra = 1
    verbose_name = "Packaging Entry"
    verbose_name_plural = "Packaging Entries"


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# SubCategory Admin
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# Brand Admin
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name")  # Display brand ID and name
    search_fields = ("name",)  # Enable search by brand name
    ordering = ("name",)  # Sort by brand name


class ProductForm(forms.ModelForm):
    prix_ttc = forms.DecimalField(
        label="Prix TTC",
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add image previews for existing images
        if self.instance and self.instance.pk:
            if self.instance.image1:
                self.fields["image1"].help_text = self.get_image_preview(
                    self.instance.image1
                )
            if self.instance.image2:
                self.fields["image2"].help_text = self.get_image_preview(
                    self.instance.image2
                )
            if self.instance.image3:
                self.fields["image3"].help_text = self.get_image_preview(
                    self.instance.image3
                )

        # Dynamically update the `prix_ttc` field based on `price_ht` and `tva`
        if (
            self.instance
            and self.instance.price_ht is not None
            and self.instance.tva is not None
        ):
            self.fields["prix_ttc"].initial = self.instance.price_ht * (
                1 + self.instance.tva / 100
            )

    def get_image_preview(self, image_field):
        """Generate HTML to display the image preview."""
        return mark_safe(f'<img src="{image_field.url}" width="150" height="150" />')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm

    list_display = (
        "product_id",
        "product_name",
        "price_ht",
        "tva",
        "get_prix_ttc",  # Use a callable for Prix TTC
        "brand",
        "category",
        "packaging_display",
        "total_stock",
        "image_thumbnail",
    )

    search_fields = ("product_name", "product_id", "brand__name")
    ordering = ("product_name",)
    list_filter = (
        "brand",
        "category",
        "subcategories",
    )

    inlines = [
        SubCategoryInline,
        StockInline,
    ]

    # readonly_fields = (
    #     "get_prix_ttc",
    # )  # Use the callable instead of assuming a DB field

    def get_readonly_fields(self, request, obj=None):
        """
        Dynamically set readonly fields.
        """
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Override save_model to update `prix_ttc` as part of the save logic.
        """
        # Recalculate `prix_ttc` if `price_ht` and `tva` are set
        if obj.price_ht is not None and obj.tva is not None:
            obj.prix_ttc = round(obj.price_ht * (1 + obj.tva / 100), 2)
        super().save_model(request, obj, form, change)

    def get_prix_ttc(self, obj):
        """
        Dynamically calculate `prix_ttc` for display in the admin interface.
        """
        if obj.price_ht is not None and obj.tva is not None:
            return round(obj.price_ht * (1 + obj.tva / 100), 2)
        return "N/A"  # Return a placeholder if the data is incomplete

    get_prix_ttc.short_description = "Prix TTC"

    def image_thumbnail(self, obj):
        """
        Display image thumbnails in the admin interface.
        """
        images = []
        if obj.image1:
            images.append(f'<img src="{obj.image1.url}" width="50" height="50" />')
        if obj.image2:
            images.append(f'<img src="{obj.image2.url}" width="50" height="50" />')
        if obj.image3:
            images.append(f'<img src="{obj.image3.url}" width="50" height="50" />')
        return mark_safe(" ".join(images)) if images else "No Images"

    image_thumbnail.short_description = "Image Previews"

    def packaging_display(self, obj):
        """
        Display the packaging in the format 'quantity x value'.
        """
        if obj.packaging:
            return (
                f"{obj.packaging.packaging_quantity} x {obj.packaging.packaging_value}"
            )
        return "N/A"

    packaging_display.short_description = "Packaging"

    def total_stock(self, obj):
        """
        Calculate and display total stock across all stores.
        """
        return sum(stock.quantity_in_stock for stock in obj.stocks.all())

    total_stock.short_description = "Total Stock"


# Stock Admin
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "store",
        "product",
        "quantity_in_stock",
        "expiration_date",
    )
    ordering = ("store",)
    search_fields = (
        "store__name",  # Search by store name
        "product__product_name",  # Search by product name
        "product__brand",  # Search by brand
    )
    list_filter = (
        "store",  # Filter by store
        "product__brand",  # Filter by brand through product
        "product__category",  # Filter by category
        "product__subcategories",  # Filter by subcategories
    )


# Store Admin
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "store_id",
        "name",
        "address",  # Display address if needed
        "city",  # Display city if needed
        "postal_code",  # Display postal code
        "phone_number",  # Display phone number
    )
    search_fields = ("name",)  # Search by store name
    ordering = ("name",)  # Order by store name


# Packaging Admin
@admin.register(Packaging)
class PackagingAdmin(admin.ModelAdmin):
    list_display = ("formatted_packaging",)  # Display formatted packaging
    search_fields = ("packaging_quantity", "packaging_value")
    ordering = ("packaging_quantity",)

    def formatted_packaging(self, obj):
        """Return the packaging formatted as 'quantity x value'."""
        return f"{obj.packaging_quantity} x {obj.packaging_value}"

    formatted_packaging.short_description = "Packaging"
