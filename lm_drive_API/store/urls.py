from django.urls import path
from .views import (
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    SubCategoryListCreateAPIView,
    SubCategoryRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("products/", ProductListCreateAPIView.as_view(), name="product-list-create"),
    path(
        "products/<str:pk>/",
        ProductRetrieveUpdateDestroyAPIView.as_view(),
        name="product-detail",
    ),
    path(
        "categories/", CategoryListCreateAPIView.as_view(), name="category-list-create"
    ),
    path(
        "categories/<str:pk>/",
        CategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="category-detail",
    ),
    path(
        "subcategories/",
        SubCategoryListCreateAPIView.as_view(),
        name="subcategory-list-create",
    ),
    path(
        "subcategories/<str:pk>/",
        SubCategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="subcategory-detail",
    ),
]
