from rest_framework import generics
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from authentication.permissions import (
    IsCustomerOrReadOnly,
)  # Import your custom permission


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsCustomerOrReadOnly]  # Allow customers to read only


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsCustomerOrReadOnly]  # Allow customers to read only


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsCustomerOrReadOnly]  # Allow customers to read only


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsCustomerOrReadOnly]  # Allow customers to read only
