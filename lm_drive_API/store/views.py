from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Product, Category, SubCategory, Stock
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    SubCategorySerializer,
    StockSerializer,
)
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

        # Extract product_id and upc from the serializer validated data
        product_id = serializer.validated_data.get(
            "product_id", product_instance.product_id
        )
        upc = serializer.validated_data.get("upc", product_instance.upc)

        # Check if another product with the same product_id already exists
        if (
            Product.objects.filter(product_id=product_id)
            .exclude(product_id=product_instance.product_id)
            .exists()
        ):
            raise ValidationError(
                f"Product with product_id '{product_id}' already exists."
            )

        # Check if another product with the same UPC already exists
        if (
            Product.objects.filter(upc=upc)
            .exclude(product_id=product_instance.product_id)
            .exists()
        ):
            raise ValidationError(f"Product with UPC '{upc}' already exists.")

        # Save the serializer (this will update the product)
        serializer.save()


class StockListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to retrieve a list of stocks and create a new stock record.
    """

    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]  # Change to your custom permission if needed

    def perform_create(self, serializer):
        product = serializer.validated_data.get("product")
        store = serializer.validated_data.get("store")

        # Check if the stock record already exists for the store and product
        if Stock.objects.filter(product=product, store=store).exists():
            raise ValidationError(
                f"Stock record for product '{product.product_name}' at store '{store.name}' already exists."
            )

        # Save the serializer (this will create the store stock)
        serializer.save()


class StockRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a stock record.
    """

    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]  # Change to your custom permission if needed

    def perform_update(self, serializer):
        product = serializer.validated_data.get("product")
        store = serializer.validated_data.get("store")

        # Check if the stock record exists for the store and product before updating
        stock_instance = self.get_object()
        if stock_instance.product != product or stock_instance.store != store:
            if Stock.objects.filter(product=product, store=store).exists():
                raise ValidationError(
                    f"Stock record for product '{product.product_name}' at store '{store.name}' already exists."
                )

        # Save the serializer (this will update the store stock)
        serializer.save()
