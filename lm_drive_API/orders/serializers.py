from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem
from authentication.models import Customer
from store.models import Product, Store
from store.serializers import ProductSerializer  # Assuming ProductSerializer exists


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(
        read_only=True
    )  # Use ProductSerializer for product details
    product_id = serializers.IntegerField(write_only=True)  # Allow writable product_id

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price"]

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product with this ID does not exist.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)  # Allow writable items
    total_amount = serializers.ReadOnlyField()  # Make total_amount read-only
    store_id = serializers.IntegerField(write_only=True)  # Allow writable store_id
    customer_id = serializers.IntegerField(
        write_only=True
    )  # Allow writable customer_id

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["order_id", "order_date", "total_amount"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        store_id = validated_data.pop("store_id", None)
        customer_id = validated_data.pop("customer_id", None)

        # Fetch and validate customer
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            raise ValidationError({"customer_id": "Customer does not exist."})

        # Fetch and validate store
        try:
            store = Store.objects.get(store_id=store_id)
        except Store.DoesNotExist:
            raise ValidationError({"store_id": "Store does not exist."})

        # Create the order
        order = Order.objects.create(customer=customer, store=store, **validated_data)

        # Add items to the order and calculate total amount
        total_amount = 0
        for item_data in items_data:
            item_data["product_id"] = item_data.pop("product_id")
            order_item = OrderItem.objects.create(order=order, **item_data)
            total_amount += order_item.quantity * order_item.price

        # Update total amount and save the order
        order.total_amount = total_amount
        order.save(update_fields=["total_amount"])

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create order items
        if items_data is not None:
            for item_data in items_data:
                item_id = item_data.get("id")
                if item_id:  # Update existing item
                    try:
                        order_item = OrderItem.objects.get(id=item_id, order=instance)
                        for attr, value in item_data.items():
                            setattr(order_item, attr, value)
                        order_item.save()
                    except OrderItem.DoesNotExist:
                        raise ValidationError(
                            {"id": f"OrderItem with id {item_id} not found."}
                        )
                else:  # Create new item
                    item_data["product_id"] = item_data.pop("product_id")
                    OrderItem.objects.create(order=instance, **item_data)

        return instance


class OrderListSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(source="customer.customer_id", read_only=True)
    store_id = serializers.CharField(source="store.store_id", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "order_date",
            "total_amount",
            "status",
            "customer_id",
            "store_id",
        ]


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(
        source="order.customer.customer_id", read_only=True
    )
    name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "name", "quantity", "customer_id"]

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save()
        return instance
