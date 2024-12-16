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
    total_ht = serializers.ReadOnlyField()  # Total HT is calculated automatically
    total_ttc = serializers.ReadOnlyField()  # Total TTC is calculated automatically

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "price_ht",
            "tva",
            "price_ttc",
            "total_ht",
            "total_ttc",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product with this ID does not exist.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)  # Allow writable items
    total_ht = serializers.ReadOnlyField()  # Make total_ht read-only
    total_ttc = serializers.ReadOnlyField()  # Make total_ttc read-only
    store_id = serializers.IntegerField(write_only=True)  # Allow writable store_id
    customer_id = serializers.IntegerField(
        write_only=True
    )  # Allow writable customer_id

    class Meta:
        model = Order
        fields = [
            "order_id",
            "customer_id",
            "store_id",
            "order_date",
            "confirmed_date",
            "fulfilled_date",
            "status",
            "total_ht",
            "total_ttc",
            "items",
        ]
        read_only_fields = ["order_id", "order_date", "total_ht", "total_ttc"]

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

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        store = validated_data.pop("store_id")
        customer = validated_data.pop("customer_id")

        with transaction.atomic():
            order = Order.objects.create(
                customer=customer, store=store, **validated_data
            )

            order_items = []
            for item_data in items_data:
                product = Product.objects.get(id=item_data["product_id"])
                item_data["price_ht"] = product.price_ht
                item_data["tva"] = product.tva
                item_data["price_ttc"] = round(
                    product.price_ht * (1 + product.tva / 100), 2
                )
                item_data["total_ht"] = round(
                    item_data["price_ht"] * item_data["quantity"], 2
                )
                item_data["total_ttc"] = round(
                    item_data["price_ttc"] * item_data["quantity"], 2
                )

                order_items.append(OrderItem(order=order, **item_data))

            OrderItem.objects.bulk_create(order_items)

            # Update totals in the order
            order.update_totals()

            return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        with transaction.atomic():
            # Update order fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update order items if provided
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
                    product = Product.objects.get(id=item_data["product_id"])
                    item_data["price_ht"] = product.price_ht
                    item_data["tva"] = product.tva
                    item_data["price_ttc"] = round(
                        product.price_ht * (1 + product.tva / 100), 2
                    )
                    item_data["total_ht"] = round(
                        item_data["price_ht"] * item_data["quantity"], 2
                    )
                    item_data["total_ttc"] = round(
                        item_data["price_ttc"] * item_data["quantity"], 2
                    )

                    if "id" in item_data:
                        order_item = OrderItem.objects.get(
                            id=item_data["id"], order=instance
                        )
                        for attr, value in item_data.items():
                            setattr(order_item, attr, value)
                        order_item.save()
                    else:
                        OrderItem.objects.create(order=instance, **item_data)

            # Update totals in the order
            instance.update_totals()

        return instance


class OrderListSerializer(serializers.ModelSerializer):
    customer_id = serializers.CharField(source="customer.customer_id", read_only=True)
    store_id = serializers.CharField(source="store.store_id", read_only=True)
    total_ht = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total_ttc = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "order_id",
            "order_date",
            "confirmed_date",
            "fulfilled_date",
            "total_ht",
            "total_ttc",
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
