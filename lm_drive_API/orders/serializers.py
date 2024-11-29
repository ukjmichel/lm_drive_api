from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem
from authentication.models import Customer
from store.models import Product, Store
from store.serializers import ProductSerializer  # Assuming ProductSerializer exists
from django.db import transaction


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

    def validate_store_id(self, value):
        try:
            return Store.objects.get(store_id=value)
        except Store.DoesNotExist:
            raise serializers.ValidationError("Store does not exist.")

    def validate_customer_id(self, value):
        try:
            return Customer.objects.get(customer_id=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer does not exist.")

    def validate_items(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list.")
        for item in value:
            if not all(key in item for key in ("product_id", "quantity", "price")):
                raise serializers.ValidationError(
                    "Each item must contain 'product_id', 'quantity', and 'price'."
                )
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        store = validated_data.pop("store_id")
        customer = validated_data.pop("customer_id")

        # Wrap in atomic transaction
        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                customer=customer, store=store, **validated_data
            )

            # Add items using bulk_create
            order_items = []
            total_amount = 0
            for item_data in items_data:
                item_data["product_id"] = item_data.pop("product_id")
                order_item = OrderItem(order=order, **item_data)
                order_items.append(order_item)
                total_amount += order_item.quantity * order_item.price

            OrderItem.objects.bulk_create(order_items)

            # Update total_amount
            order.total_amount = total_amount
            order.save(update_fields=["total_amount"])

            return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        updated_fields = {}  # Track updated fields

        # Wrap in atomic transaction
        with transaction.atomic():
            # Update order fields
            for attr, value in validated_data.items():
                if getattr(instance, attr) != value:  # Check if the field has changed
                    setattr(instance, attr, value)
                    updated_fields[attr] = value  # Track the updated field
            instance.save()

            # Update or create order items
            if items_data is not None:
                current_item_ids = {
                    item.get("id") for item in items_data if "id" in item
                }
                existing_items = {item.id for item in instance.items.all()}

                # Delete items not in the payload
                OrderItem.objects.filter(
                    order=instance, id__in=existing_items - current_item_ids
                ).delete()

                for item_data in items_data:
                    item_id = item_data.get("id")
                    if item_id:  # Update existing item
                        order_item = OrderItem.objects.get(id=item_id, order=instance)
                        for attr, value in item_data.items():
                            if (
                                getattr(order_item, attr) != value
                            ):  # Check if the field has changed
                                setattr(order_item, attr, value)
                        order_item.save()
                    else:  # Create new item
                        item_data["product_id"] = item_data.pop("product_id")
                        OrderItem.objects.create(order=instance, **item_data)

                updated_fields["items"] = items_data  # Include updated items

        # Track updated fields (for logging or debugging)
        instance.updated_fields = updated_fields  # Temporary attribute
        return instance  # Return the updated instance


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
