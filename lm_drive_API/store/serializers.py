import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory, Stock, Packaging, Brand


class BaseCategorySerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if "id" in data:
            try:
                category = self.Meta.model.objects.get(id=data["id"])
                return {
                    "id": category.id,
                    "name": category.name,
                }
            except self.Meta.model.DoesNotExist:
                raise ValidationError(
                    f"{self.Meta.model.__name__} with this ID does not exist."
                )

        if "name" in data:
            try:
                category = self.Meta.model.objects.get(name=data["name"])
                return {
                    "id": category.id,
                    "name": category.name,
                }
            except self.Meta.model.DoesNotExist:
                # If not found, let the base method handle the data
                return super().to_internal_value(data)

        raise ValidationError(
            f"{self.Meta.model.__name__} must have either an 'id' or 'name'."
        )


class CategorySerializer(BaseCategorySerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class SubCategorySerializer(BaseCategorySerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]  # Fields you want to include in the API response


class PackagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packaging
        fields = [
            "packaging_quantity",
            "packaging_value",
            "packaging_type",
        ]


class ProductSerializer(serializers.ModelSerializer):
    brand = serializers.SlugRelatedField(
        queryset=Brand.objects.all(),
        slug_field="name",  # This will display the brand's name instead of ID
    )
    category = CategorySerializer()
    subcategories = SubCategorySerializer(many=True)
    stock_summary = (
        serializers.SerializerMethodField()
    )  # Custom field for stock summary
    packaging = PackagingSerializer()  # Add packaging field

    class Meta:
        model = Product
        fields = [
            "product_id",
            "product_name",
            "upc",
            "description",
            "price",
            "brand",
            "category",
            "subcategories",
            "image",
            "packaging",  # Include packaging in the output
            "stock_summary",  # Include stock summary in the output
        ]

    def get_stock_summary(self, obj):
        """
        Get the total stock and stock details related to the product.
        Returns a dictionary with total stock and stock for different stores.
        """
        return obj.get_stock_summary()  # Call the method to retrieve stock summary

    def to_representation(self, instance):
        """
        Customize the representation of the product data.
        Stock summary and price are only visible to authenticated users.
        """
        # Get the initial representation from the parent class
        representation = super().to_representation(instance)

        # Retrieve the request from the context to check if the user is authenticated
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Add stock summary and price if the user is authenticated
            representation["stock_summary"] = self.get_stock_summary(instance)
            representation["price"] = instance.price
        else:
            # Remove stock summary and price for unauthenticated users
            representation.pop("stock_summary", None)
            representation.pop("price", None)

        # Add image URL to the representation, handling cases where image or request might be missing
        representation["image_url"] = self.get_image_url(instance)

        return representation

    def get_image_url(self, obj):
        """
        Build the absolute URL for the product image, if available.
        """
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def create(self, validated_data):
        """
        Create a new product instance.
        """
        packaging_data = validated_data.pop("packaging")  # Extract packaging data
        product_id = validated_data.get("product_id")
        upc = validated_data.get("upc")

        # Check for existing product_id or UPC
        if Product.objects.filter(product_id=product_id).exists():
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )
        if Product.objects.filter(upc=upc).exists():
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Handle main category
        category_data = validated_data.pop("category")
        category, _ = Category.objects.get_or_create(name=category_data["name"])

        # Handle subcategories
        subcategories_data = validated_data.pop("subcategories", [])
        subcategory_objs = [
            SubCategory.objects.get_or_create(name=subcategory_data["name"])[0]
            for subcategory_data in subcategories_data
        ]

        # Handle packaging
        packaging, _ = Packaging.objects.get_or_create(
            packaging_quantity=packaging_data["packaging_quantity"],
            packaging_value=packaging_data["packaging_value"],
            packaging_type=packaging_data["packaging_type"],
        )

        # Create product
        product = Product.objects.create(
            category=category, packaging=packaging, **validated_data
        )
        product.subcategories.set(subcategory_objs)  # Set subcategories
        return product

    def update(self, instance, validated_data):
        """
        Update an existing product instance.
        """
        # Extract packaging data if it exists
        packaging_data = validated_data.pop("packaging", None)
        if packaging_data:
            # Update or create packaging
            packaging, _ = Packaging.objects.get_or_create(
                packaging_quantity=packaging_data["packaging_quantity"],
                packaging_value=packaging_data["packaging_value"],
                packaging_type=packaging_data["packaging_type"],
            )
            instance.packaging = packaging  # Set the updated packaging

        # Handle category
        category_data = validated_data.pop("category", None)
        if category_data:
            category, _ = Category.objects.get_or_create(name=category_data["name"])
            instance.category = category  # Set the updated category

        # Handle subcategories
        subcategories_data = validated_data.pop("subcategories", [])
        if subcategories_data:
            subcategory_objs = [
                SubCategory.objects.get_or_create(name=subcategory_data["name"])[0]
                for subcategory_data in subcategories_data
            ]
            instance.subcategories.set(
                subcategory_objs
            )  # Set the updated subcategories

        # Update product fields
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()  # Save the updated product
        return instance


class StockSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(
        source="store.name", read_only=True
    )  # Read-only to fetch store name

    class Meta:
        model = Stock
        fields = [
            "store",  # Optional, if you want to return the store object
            "store_name",  # Return the name of the store
            "product",  # Optional, if you want to return the product object
            "quantity_in_stock",
            "expiration_date",
        ]
        read_only_fields = [
            "id"
        ]  # Make 'id' read-only if you don't want it to be included in POST requests

    def create(self, validated_data):
        """
        Create a new Stock instance.
        """
        stock = Stock.objects.create(**validated_data)
        return stock

    def update(self, instance, validated_data):
        """
        Update an existing Stock instance.
        """
        instance.store = validated_data.get("store", instance.store)
        instance.product = validated_data.get("product", instance.product)
        instance.quantity_in_stock = validated_data.get(
            "quantity_in_stock", instance.quantity_in_stock
        )
        instance.expiration_date = validated_data.get(
            "expiration_date", instance.expiration_date
        )
        instance.save()
        return instance

    def validate_quantity_in_stock(self, value):
        """
        Validate that the quantity in stock is not negative.
        """
        if value < 0:
            raise serializers.ValidationError("Quantity in stock cannot be negative.")
        return value

    def validate_expiration_date(self, value):
        """
        Validate that the expiration date is in the future.
        """
        if value < datetime.date.today():
            raise serializers.ValidationError("Expiration date must be in the future.")
        return value
