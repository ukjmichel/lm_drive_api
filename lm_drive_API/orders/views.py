from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from authentication.permissions import IsCustomerOrAdmin
from authentication.models import Customer
from rest_framework.exceptions import ValidationError
from store.models import Product


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsCustomerOrAdmin]

    def create(self, request, *args, **kwargs):
        validated_data = request.data
        items_data = validated_data.pop("items", [])

        # Check if customer_id is provided directly instead of in a nested "customer" dict
        customer_id = validated_data.get("customer_id")
        if not customer_id:
            raise ValidationError({"customer_id": "This field is required."})

        # Fetch the customer instance using customer_id or return 404
        customer = get_object_or_404(Customer, customer_id=customer_id)

        # Check for existing pending orders for the customer
        existing_order = Order.objects.filter(
            customer=customer, status="pending"
        ).first()

        if existing_order:
            return Response(
                OrderSerializer(existing_order).data,
                status=status.HTTP_200_OK,
            )  # Return existing order if found

        # Create new order with status 'pending'
        order = Order.objects.create(
            customer=customer, status="pending", **validated_data
        )

        # Create order items if provided
        total_amount = 0
        for item_data in items_data:
            order_item = OrderItem.objects.create(order=order, **item_data)
            total_amount += order_item.total  # Use the calculated total from OrderItem

        # Save total amount to the order after items have been created
        order.total_amount = total_amount
        order.save(update_fields=["total_amount"])

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        """Filter orders based on the user's permissions."""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(
            customer__user=self.request.user
        )  # Adjust to match customer relationship


class OrderRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsCustomerOrAdmin]
    lookup_field = "order_id"  # Ensure this matches your URL pattern

    def delete(self, request, *args, **kwargs):
        """Allow deletion only by staff or the order owner."""
        order = self.get_object()  # Retrieve the order object
        # Check if the user is staff or the order owner
        if not request.user.is_staff and order.customer.user != request.user:
            return Response(
                {"error": "Only staff or the order owner can delete this order."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order.delete()  # Delete the order
        return Response(
            {"message": "Order deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def patch(self, request, *args, **kwargs):
        """Allow partial updates to the order."""
        order = self.get_object()  # Retrieve the order object
        if not request.user.is_staff and order.customer.user != request.user:
            return Response(
                {"error": "Only staff or the order owner can update this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # Save the updated order
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        """Filter orders based on the user's permissions."""
        if self.request.user.is_staff:
            return Order.objects.all()  # Staff can see all orders
        return Order.objects.filter(
            customer__user=self.request.user
        )  # Customers can see their own orders


class OrderItemListView(generics.ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsCustomerOrAdmin]

    def get_queryset(self):
        """Filter order items based on the order ID and user's permissions."""
        order_id = self.kwargs.get("order_id")
        if order_id:
            order = Order.objects.filter(order_id=order_id).first()
            if order and (
                self.request.user.is_staff or order.customer.user == self.request.user
            ):
                return OrderItem.objects.filter(order=order)
        return (
            OrderItem.objects.none()
        )  # Return empty queryset if no valid order_id is provided


class AddOrderItemView(generics.CreateAPIView):
    serializer_class = OrderItemSerializer

    def post(self, request, order_id, *args, **kwargs):
        # Extract product_id and quantity from request data
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)  # Default quantity to 1

        # Try to get the product by product_id
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": f"No product found with product_id: {product_id}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch the order using the order_id
        order = get_object_or_404(Order, order_id=order_id)

        # Check if the OrderItem already exists
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"quantity": quantity, "price": product.price},
        )

        if not created:
            # If it already exists, update the quantity
            order_item.quantity += quantity
            order_item.save()

        return Response(
            OrderItemSerializer(order_item).data, status=status.HTTP_201_CREATED
        )
