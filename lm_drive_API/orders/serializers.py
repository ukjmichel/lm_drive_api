from rest_framework import serializers
from .models import Order, OrderItem
from authentication.models import Customer
from store.serializers import ProductSerializer  # Assuming you have a ProductSerializer
from rest_framework.exceptions import ValidationError
from store.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(
        read_only=True
    )  # Use ProductSerializer for product details

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",  # Adjusted to serialize the entire product
            "quantity",
            "price",
        ]

    def validate_product_id(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        if not Product.objects.filter(product_id=value).exists():
            raise serializers.ValidationError("Product with this ID does not exist.")
        return value


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

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update the order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Handle updating the items if provided
        if items_data is not None:
            # Update existing order items or create new ones
            for item_data in items_data:
                order_item_id = item_data.get("id", None)
                if order_item_id:  # Update existing order item
                    order_item = get_object_or_404(
                        OrderItem, id=order_item_id, order=instance
                    )
                    for attr, value in item_data.items():
                        setattr(order_item, attr, value)
                    order_item.save()
                else:  # Create a new order item
                    OrderItem.objects.create(order=instance, **item_data)

        return instance


class OrderListSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(
        source="order.customer.customer_id", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "order_id",
            "order_date",
            "total_amount",
            "status",
            "customer_id",
        ]  # Include customer_id

    def get_customer_id(self, obj):
        return obj.customer.customer_id  # Adjust based on your customer field name


from rest_framework import serializers
from .models import OrderItem


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(
        source="order.customer.customer_id", read_only=True
    )
    name = serializers.CharField(
        source="product.name", read_only=True
    )  # Assuming you have a name field in Product

    class Meta:
        model = OrderItem
        fields = ["id", "name", "quantity", "customer_id"]

    def update(self, instance, validated_data):
        # Update only the quantity field
        instance.quantity = validated_data.get("quantity", instance.quantity)

        # Validate that quantity is not negative
        if instance.quantity < 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity cannot be negative."}
            )

        instance.save()
        return instance
