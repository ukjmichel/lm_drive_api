from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory
from .serializers import ProductSerializer, CategorySerializer, SubCategorySerializer
from authentication.permissions import IsStaffOrReadOnly
import logging




class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        # Validate the data
        category_name = serializer.validated_data.get("name")

        # Check if a category with the same name already exists
        if Category.objects.filter(name=category_name).exists():
            raise ValidationError(
                f"Category with name '{category_name}' already exists."
            )

        # Save the serializer (this will create the category)
        serializer.save()


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        # Get the existing category instance
        category_instance = self.get_object()

        # Validate the data
        category_name = serializer.validated_data.get("name")

        # Check if a category with the same name already exists and is not the current instance
        if (
            Category.objects.filter(name=category_name)
            .exclude(id=category_instance.id)
            .exists()
        ):
            raise ValidationError(
                f"Category with name '{category_name}' already exists."
            )

        # Save the serializer (this will update the category)
        serializer.save()


class SubCategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        # Get the name of the subcategory from the validated data
        subcategory_name = serializer.validated_data.get("name")

        # Check if a subcategory with the same name already exists
        if SubCategory.objects.filter(name=subcategory_name).exists():
            raise ValidationError(
                f"SubCategory with name '{subcategory_name}' already exists."
            )

        # Save the serializer (this will create the subcategory)
        serializer.save()


class SubCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        # Get the name of the subcategory from the validated data
        subcategory_name = serializer.validated_data.get("name")

        # Check if a subcategory with the same name already exists
        if SubCategory.objects.filter(name=subcategory_name).exists():
            raise ValidationError(
                f"SubCategory with name '{subcategory_name}' already exists."
            )

        # Save the serializer (this will create the subcategory)
        serializer.save()


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        product_id = serializer.validated_data.get("product_id")
        upc = serializer.validated_data.get("upc")

        # Check if a product with the same product_id or UPC already exists
        if Product.objects.filter(product_id=product_id).exists():
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        if Product.objects.filter(upc=upc).exists():
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Save the serializer (this will create the product)
        serializer.save()


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_update(self, serializer):
        # Get the existing product instance
        product_instance = self.get_object()

        product_id = serializer.validated_data.get(
            "product_id", product_instance.product_id
        )
        upc = serializer.validated_data.get("upc", product_instance.upc)

        # Check if another product with the same product_id or UPC already exists
        if (
            Product.objects.filter(product_id=product_id)
            .exclude(id=product_instance.id)
            .exists()
        ):
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        if Product.objects.filter(upc=upc).exclude(id=product_instance.id).exists():
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Save the serializer (this will update the product)
        serializer.save()
