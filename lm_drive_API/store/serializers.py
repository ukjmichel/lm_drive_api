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
            "upc",
            "description",
            "price",
            "stock",
            "brand",
            "category",
            "image",
        ]

    def create(self, validated_data):
        category_data = validated_data.pop("category")
        category, created = Category.objects.get_or_create(**category_data)
        product = Product.objects.create(category=category, **validated_data)
        return product

    def update(self, instance, validated_data):
        category_data = validated_data.pop("category", None)
        if category_data:
            category, created = Category.objects.get_or_create(**category_data)
            instance.category = category
        instance.product_id = validated_data.get("product_id", instance.product_id)
        instance.upc = validated_data.get("upc", instance.upc)
        instance.description = validated_data.get("description", instance.description)
        instance.price = validated_data.get("price", instance.price)
        instance.stock = validated_data.get("stock", instance.stock)
        instance.brand = validated_data.get("brand", instance.brand)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        return instance
