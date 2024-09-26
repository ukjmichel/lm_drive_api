from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"  # Include all fields in the serializer


class OrderSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(
        source="get_total_amount", read_only=True, max_digits=10, decimal_places=2
    )

    class Meta:
        model = Order
        fields = (
            "order_id",
            "customer",
            "address",
            "created_at",
            "updated_at",
            "status",
            "total_amount",
            "items",
        )
        depth = 1  # Include nested OrderItem data

    def get_total_amount(self, obj):
        return obj.calculate_total_amount()  # Call the calculate_total_amount method
