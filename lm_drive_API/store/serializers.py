from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory


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


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    subcategories = SubCategorySerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "product_id",
            "product_name",
            "upc",
            "description",
            "price",
            "stock",
            "brand",
            "category",
            "subcategories",
            "image",
        ]

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
        product_id = validated_data.get("product_id", instance.product_id)
        upc = validated_data.get("upc", instance.upc)

        # Check if another product with the same product_id or UPC already exists
        if (
            Product.objects.filter(product_id=product_id)
            .exclude(id=instance.id)
            .exists()
        ):
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        if Product.objects.filter(upc=upc).exclude(id=instance.id).exists():
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Update main category
        category_data = validated_data.pop("category", None)
        if category_data:
            category, created = Category.objects.get_or_create(
                name=category_data["name"]
            )

            instance.category = category

        # Update subcategories
        subcategories_data = validated_data.pop("subcategories", [])
        if subcategories_data is not None:
            instance.subcategories.clear()  # Clear existing subcategories
            for subcategory_data in subcategories_data:
                subcategory, created = SubCategory.objects.get_or_create(
                    name=subcategory_data["name"]
                )

                instance.subcategories.add(subcategory)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
