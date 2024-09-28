from django.urls import path
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
    ),  # Retrieve, update, and delete an order
    path(
        "<str:order_id>/items/",
        AddOrderItemView.as_view(),
        name="add-order-item",
    ),  # Add an item to an order
]
