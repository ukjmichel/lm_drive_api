from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    AddOrderItemView,
    OrderItemRetrieveUpdateDestroyView,
)

urlpatterns = [
    path(
        "", OrderListCreateView.as_view(), name="order-list-create"
    ),  # List and create orders
    path(
        "<str:order_id>/", OrderDetailView.as_view(), name="order-detail"
    ),  # Retrieve, update, and delete an order using order_id
    path(
        "<str:order_id>/add-item/",
        AddOrderItemView.as_view(),
        name="add-item-to-order",
    ),
    path(
        "<str:order_id>/item/<int:id>/",
        OrderItemRetrieveUpdateDestroyView.as_view(),
        name="order-item-update",
    ),
]
