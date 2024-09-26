from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from authentication.permissions import IsOwnerOrAdmin


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdmin]


class OrderItemListView(generics.ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        order_id = self.kwargs.get("order_id")
        if order_id:
            return OrderItem.objects.filter(order__order_id=order_id)
        return OrderItem.objects.none()  # Return empty queryset if no order_id provided
