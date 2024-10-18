from rest_framework import serializers
from .models import Payment
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(write_only=True)  # Input order ID
    customer_id = serializers.CharField(read_only=True)  # Output customer ID
    stripe_customer_id = serializers.CharField(
        read_only=True
    )  # Output stripe customer ID

    class Meta:
        model = Payment
        fields = [
            "order_id",
            "payment_method_id",
            "amount",
            "currency",
            "customer_id",
            "stripe_customer_id",
        ]  # Expose customer_id and stripe_customer_id as read-only

    def validate(self, data):
        # Get the order instance using the provided order_id
        try:
            order = Order.objects.get(order_id=data["order_id"])
            data["order"] = order  # Add the Order instance to validated data
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                {"order_id": "Order with this ID does not exist."}
            )

        # Automatically fetch customer details from the Order model
        customer = order.customer
        if not customer:
            raise serializers.ValidationError(
                {"customer": "Order has no associated customer."}
            )

        # Retrieve customer_id and stripe_customer_id from the related Customer model
        data["customer_id"] = customer.customer_id
        data["stripe_customer_id"] = customer.stripe_customer_id

        return data

    def create(self, validated_data):
        # Remove read-only fields before saving
        validated_data.pop("customer_id", None)
        validated_data.pop("stripe_customer_id", None)

        # Create the payment record
        return super().create(validated_data)
