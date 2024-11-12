from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    payment_date = serializers.DateTimeField(
        source="created_at", read_only=True
    )  # Use created_at as payment_date

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "payment_date",
            "payment_method_id",
            "status",  # Optional: Expose payment status if useful
        ]
        read_only_fields = ["id", "payment_date", "status"]

    def validate_amount(self, value):
        """Check that the amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        """Create and return a new `Payment` instance, given the validated data."""
        return Payment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update and return an existing `Payment` instance, given the validated data."""
        instance.amount = validated_data.get("amount", instance.amount)
        instance.payment_method_id = validated_data.get(
            "payment_method_id", instance.payment_method_id
        )
        instance.save()
        return instance
