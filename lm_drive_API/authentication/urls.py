from django.urls import path
from .views import (
    CustomerListCreateAPIView,  # Combines list and create
    CustomerRetrieveUpdateDestroyAPIView,  # Combines retrieve, update, and delete
)

urlpatterns = [
    path(
        "customers/", CustomerListCreateAPIView.as_view(), name="customer-list-create"
    ),  # List customers and create a customer
    path(
        "customers/<str:customer_id>/",  # Use `customer_id` directly in the path
        CustomerRetrieveUpdateDestroyAPIView.as_view(),
        name="customer-detail",
    ),  # Retrieve, update, and delete a customer
]
