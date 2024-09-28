from rest_framework import serializers
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()  # Nested serializer for category

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
            "image",
        ]

    def create(self, validated_data):
        # Extract the nested category data from validated data
        category_data = validated_data.pop("category")
        # Find or create the category based on the provided data
        category, _ = Category.objects.get_or_create(**category_data)
        # Create the product with the associated category
        product = Product.objects.create(category=category, **validated_data)
        return product

    def update(self, instance, validated_data):
        # Handle category update separately, if provided
        category_data = validated_data.pop("category", None)
        if category_data:
            # Update or create the category
            category, _ = Category.objects.get_or_create(**category_data)
            instance.category = category

        # Update the other fields on the Product instance
        instance.product_id = validated_data.get("product_id", instance.product_id)
        instance.product_name = validated_data.get(
            "product_name", instance.product_name
        )
        instance.upc = validated_data.get("upc", instance.upc)
        instance.description = validated_data.get("description", instance.description)
        instance.price = validated_data.get("price", instance.price)
        instance.stock = validated_data.get("stock", instance.stock)
        instance.brand = validated_data.get("brand", instance.brand)
        instance.image = validated_data.get("image", instance.image)

        # Save the changes to the product
        instance.save()
        return instance
