from django.urls import path
from .views import (
    BrandListView,
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    SubCategoryListCreateAPIView,
    SubCategoryRetrieveUpdateDestroyAPIView,
    StockListCreateAPIView,
    StockRetrieveUpdateDestroyAPIView,
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
    # List and create stock records for a specific store
    path(
        "<str:store_id>/stocks/",
        StockListCreateAPIView.as_view(),
        name="store-stock-list-create",
    ),
    # Retrieve, update, and delete a specific stock record for a store (using stock ID and store ID)
    path(
        "<str:store_id>/stocks/<str:product_id>/",  # Ensure store_id and product_id match exactly
        StockRetrieveUpdateDestroyAPIView.as_view(),
        name="product-stock-retrieve-update-destroy",
    ),
    path(
        "brands/", BrandListView.as_view(), name="brand-list"
    ),  # Endpoint for listing brands
]
