from django.urls import path
from . import views  # Import views from your orders.views.py

urlpatterns = [
    path(
        "", views.OrderListCreateView.as_view(), name="order-list"
    ),  # List and create orders
    path(
        "<str:order_id>/",
        views.OrderRetrieveUpdateDestroyView.as_view(),
        name="order-detail",
    ),  # Retrieve, update, delete orders
    path(
        "<str:order_id>/items/", views.OrderItemListView.as_view(), name="order-items"
    ),  # Retrieve order items
]
