from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory, Stock


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]

    def to_internal_value(self, data):
        # Check for ID first, and return the ID if it exists
        if "id" in data:
            try:
                category = Category.objects.get(id=data["id"])
                return {
                    "id": category.id,
                    "name": category.name,
                }  # Return dict with existing category data
            except Category.DoesNotExist:
                raise serializers.ValidationError(
                    "Category with this ID does not exist."
                )

        # Check for name, and return the name if it exists
        if "name" in data:
            try:
                category = Category.objects.get(name=data["name"])
                return {
                    "id": category.id,
                    "name": category.name,
                }  # Return dict with existing category data
            except Category.DoesNotExist:
                # If not found, let the base method handle the data
                return super().to_internal_value(data)

        # Raise error if neither id nor name are present
        raise serializers.ValidationError(
            "Category must have either an 'id' or 'name'."
        )


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name"]

    def to_internal_value(self, data):
        # Check for ID first, and return the ID if it exists
        if "id" in data:
            try:
                subcategory = SubCategory.objects.get(id=data["id"])
                return {
                    "id": subcategory.id,
                    "name": subcategory.name,
                }  # Return dict with existing subcategory data
            except SubCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "SubCategory with this ID does not exist."
                )

        # Check for name, and return the name if it exists
        if "name" in data:
            try:
                subcategory = SubCategory.objects.get(name=data["name"])
                return {
                    "id": subcategory.id,
                    "name": subcategory.name,
                }  # Return dict with existing subcategory data
            except SubCategory.DoesNotExist:
                # If not found, let the base method handle the data
                return super().to_internal_value(data)

        # Raise error if neither id nor name are present
        raise serializers.ValidationError(
            "SubCategory must have either an 'id' or 'name'."
        )


from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    subcategories = SubCategorySerializer(many=True)
    stock = serializers.SerializerMethodField()  # Custom field for stock information

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
            "stock",  # Include stock in the output
        ]
        read_only_fields = ["stock"]  # Make stock read-only

    def get_stock(self, obj):
        """
        Get all stock details related to the product.
        Returns an array of stock for different stores.
        """
        stock_entries = Stock.objects.filter(
            product=obj
        )  # Fetch all stock related to the product
        return StockSerializer(
            stock_entries, many=True
        ).data  # Serialize all stock entries as a list

    def to_representation(self, instance):
        """
        Customize the representation of the product data.
        Stock is only visible to authenticated users.
        """
        representation = super().to_representation(instance)

        # Check if the user is authenticated from the request context
        request = self.context.get("request", None)
        if request and request.user.is_authenticated:
            representation["stock"] = self.get_stock(
                instance
            )  # Include stock if authenticated
        else:
            representation.pop("stock", None)  # Remove stock if not authenticated

        return representation

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def create(self, validated_data):
        product_id = validated_data.get("product_id")
        upc = validated_data.get("upc")

        # Check if a product with the same product_id or UPC already exists
        if Product.objects.filter(product_id=product_id).exists():
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        if Product.objects.filter(upc=upc).exists():
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Handle main category
        category_data = validated_data.pop("category")
        category, created = Category.objects.get_or_create(name=category_data["name"])

        # Handle subcategories
        subcategories_data = validated_data.pop("subcategories", [])
        subcategory_objs = []
        for subcategory_data in subcategories_data:
            subcategory, created = SubCategory.objects.get_or_create(
                name=subcategory_data["name"]
            )
            subcategory_objs.append(subcategory)

        # Create product
        product = Product.objects.create(category=category, **validated_data)
        product.subcategories.set(subcategory_objs)
        return product

    def update(self, instance, validated_data):
        # Update main category
        category_data = validated_data.pop("category", None)
        if category_data:
            category, created = Category.objects.get_or_create(
                name=category_data["name"]
            )
            instance.category = category

        # Update subcategories
        subcategories_data = validated_data.pop("subcategories", [])
        if subcategories_data:
            subcategory_objs = []
            for subcategory_data in subcategories_data:
                subcategory, created = SubCategory.objects.get_or_create(
                    name=subcategory_data["name"]
                )
                subcategory_objs.append(subcategory)
            instance.subcategories.set(subcategory_objs)

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["store", "product", "quantity_in_stock", "expiration_date"]

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

    # Removed duplicate Meta class definition
    class Meta:
        model = Stock  # Corrected to use Stock
        fields = [
            "store",
            "product",
            "quantity_in_stock",
            "expiration_date",
        ]  # Include relevant fields
        read_only_fields = [
            "id"
        ]  # Optionally make id read-only if you don't want it to be included in POST requests

    def validate_quantity_in_stock(self, value):
        """Ensure that the quantity in stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Quantity in stock cannot be negative.")
        return value
