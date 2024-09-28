from rest_framework import serializers
from .models import Order, OrderItem
from authentication.models import Customer
from rest_framework.exceptions import ValidationError


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ["total"]  # Make total read-only, calculated on save


from rest_framework.exceptions import ValidationError


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)  # Allow writable items
    total_amount = serializers.ReadOnlyField()  # Make total_amount read-only

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [
            "order_id",
            "order_date",
            "total_amount",  # Mark total_amount as read-only
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])

        # Change this to directly get customer_id
        customer_id = validated_data.get("customer_id")
        if not customer_id:
            raise ValidationError({"customer_id": "This field is required."})

        # Fetch the customer using the provided customer_id
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            raise ValidationError({"customer_id": "Customer does not exist."})

        # Check for existing pending orders for the customer
        existing_order = Order.objects.filter(
            customer=customer, status="pending"
        ).first()

        if existing_order:
            return existing_order  # Return existing order if found

        # Create new order with status 'pending'
        order = Order.objects.create(
            customer=customer, status="pending", **validated_data
        )

        # If items are provided, create order items
        if items_data:
            total_amount = 0
            for item_data in items_data:
                order_item = OrderItem.objects.create(order=order, **item_data)
                total_amount += (
                    order_item.total
                )  # Use the calculated total from OrderItem

            # Save total amount to the order after items have been created
            order.total_amount = total_amount
            order.save(update_fields=["total_amount"])

        return order
