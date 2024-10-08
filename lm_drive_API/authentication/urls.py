from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
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
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),  # Token refresh view
]
