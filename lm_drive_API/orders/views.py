from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from authentication.permissions import IsCustomerOrAdmin
from authentication.models import Customer
from store.models import Product


class OrderListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating orders.
    Customers can only create their own orders.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsCustomerOrAdmin]

    def create(self, request, *args, **kwargs):
        validated_data = request.data
        items_data = validated_data.pop("items", [])

        # Ensure 'customer_id' is provided
        customer_id = request.data.get("customer_id")
        if not customer_id:
            raise ValidationError({"customer_id": "This field is required."})

        # Fetch the customer instance or raise 404
        customer = get_object_or_404(
            Customer, customer_id=customer_id
        )  # Use customer_id

        # Check if there are any pending orders for this customer
        existing_order = Order.objects.filter(
            customer=customer, status="pending"
        ).first()

        if existing_order:
            return Response(
                OrderSerializer(existing_order).data,
                status=status.HTTP_200_OK,
            )  # Return existing order if found

        # Create a new order with status 'pending'
        order = Order.objects.create(
            customer=customer, status="pending", **validated_data
        )

        # Create order items and calculate total amount
        total_amount = 0
        for item_data in items_data:
            # Get the product from the item data or raise error
            product = get_object_or_404(
                Product, product_id=item_data["product_id"]
            )  # Use product_id
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data.get("quantity", 1),  # Default quantity to 1
                price=product.price,
            )
            total_amount += order_item.quantity * order_item.price

        # Update the order with the total amount
        order.total_amount = total_amount
        order.save(update_fields=["total_amount"])

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        """
        Filter orders based on the user's permissions.
        Staff can see all orders, customers can only see their own orders.
        """
        if self.request.user.is_staff:
            return Order.objects.all()  # Staff can see all orders
        return Order.objects.filter(customer__user=self.request.user)


class OrderRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating, or deleting a specific order.
    Only the order owner or staff can perform these actions.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsCustomerOrAdmin]
    lookup_field = "order_id"

    def delete(self, request, *args, **kwargs):
        """Allow deletion only by staff or the order owner."""
        order = self.get_object()  # Retrieve the order object
        if not request.user.is_staff and order.customer.user != request.user:
            return Response(
                {"error": "Only staff or the order owner can delete this order."},
                status=status.HTTP_403_FORBIDDEN,
            )
        order.delete()
        return Response(
            {"message": "Order deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def patch(self, request, *args, **kwargs):
        """Allow partial updates to the order."""
        order = self.get_object()
        if not request.user.is_staff and order.customer.user != request.user:
            return Response(
                {"error": "Only staff or the order owner can update this order."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        """Filter orders based on the user's permissions."""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer__user=self.request.user)


class OrderItemListView(generics.ListAPIView):
    """
    View for listing order items associated with a specific order.
    Only the order owner or staff can access this list.
    """

    serializer_class = OrderItemSerializer
    permission_classes = [IsCustomerOrAdmin]

    def get_queryset(self):
        """Filter order items based on the order ID and user's permissions."""
        order_id = self.kwargs.get("order_id")
        order = get_object_or_404(Order, order_id=order_id)
        if self.request.user.is_staff or order.customer.user == self.request.user:
            return OrderItem.objects.filter(order=order)
        return OrderItem.objects.none()  # Return empty if no access


class AddOrderItemView(generics.CreateAPIView):
    """
    View for adding an item to an existing order.
    """

    serializer_class = OrderItemSerializer

    def post(self, request, *args, **kwargs):
        # Extract order_id, product_id, and quantity from request data
        order_id = request.data.get("order_id")
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)  # Default quantity to 1

        # Get the product by product_id or raise error
        product = get_object_or_404(Product, product_id=product_id)

        # Fetch the order using the order_id or raise error
        order = get_object_or_404(Order, order_id=order_id)  # Use order_id

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
