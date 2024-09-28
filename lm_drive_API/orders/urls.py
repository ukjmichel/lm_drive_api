from django.urls import path
from . import views  # Import views from your orders.views.py
from .views import (
    OrderListCreateView,
    OrderRetrieveUpdateDestroyView,
    AddOrderItemView,
)

urlpatterns = [
    path(
        "", OrderListCreateView.as_view(), name="order-list-create"
    ),  # List and create orders
    path(
        "<str:order_id>/",
        OrderRetrieveUpdateDestroyView.as_view(),
        name="order-detail",
    ),  # Retrieve, update, delete orders
    path(
        "<str:order_id>/items/",
        AddOrderItemView.as_view(),
        name="add-order-item",
    ),  # Retrieve order items
]
