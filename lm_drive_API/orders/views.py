from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
)
from authentication.models import Customer
from store.models import Product


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            # Staff can see all orders
            return Order.objects.all()
        else:
            # Customers can see their own orders
            try:
                customer = Customer.objects.get(user=user)
                return Order.objects.filter(customer=customer)
            except Customer.DoesNotExist:
                return (
                    Order.objects.none()
                )  # Return an empty queryset if customer doesn't exist

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_staff:
            # Admins can specify the customer when creating an order
            customer_id = self.request.data.get("customer_id")
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                raise serializers.ValidationError(
                    "The specified customer does not exist."
                )

            # Save the order with the specified customer
            serializer.save(customer=customer)

        else:
            # Regular customers can only create orders for themselves
            try:
                customer = Customer.objects.get(user=user)
            except Customer.DoesNotExist:
                raise serializers.ValidationError(
                    "You must be a registered customer to place an order."
                )

            # Check if the customer already has a pending order
            if Order.objects.filter(customer=customer, status="pending").exists():
                raise serializers.ValidationError(
                    "A customer can only have one pending order at a time."
                )

            # Save the order with the associated customer
            serializer.save(customer=customer)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"

    def get_queryset(self):
        user = self.request.user  # Get the authenticated user

        # If the user is staff, return all orders
        if user.is_staff:
            return Order.objects.all()

        # Fetch the Customer instance related to the user
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            raise NotFound("Customer does not exist.")

        # Filter orders by the customer's ID
        return Order.objects.filter(customer=customer)

    def perform_update(self, serializer):
        order = self.get_object()  # Get the current order instance
        new_status = serializer.validated_data.get(
            "status"
        )  # Get the status the user is trying to set

        # Check if the user is not staff and also not the owner of the order
        if not self.request.user.is_staff and order.customer.user != self.request.user:
            raise PermissionDenied("You do not have permission to update this order.")

        # If the user is not staff, ensure the order is still pending and status is set to 'confirmed'
        if not self.request.user.is_staff:
            if order.status != "pending":
                raise PermissionDenied(
                    "You cannot update this order because it is not pending."
                )
            if new_status != "confirmed":
                raise PermissionDenied(
                    "Non-staff users can only set the status to 'confirmed'."
                )

        # Staff can update the order freely, without these restrictions
        serializer.save()  # Proceed with the update

    def perform_destroy(self, instance):
        # Allow staff to delete orders
        if self.request.user.is_staff:
            instance.delete()
        else:
            raise PermissionDenied("Only staff can delete orders.")


class AddOrderItemView(generics.CreateAPIView):
    """
    View for adding an item to an existing order.
    Only the owner of the order or an admin can access this view.
    """

    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get_order_and_product(self, order_id, product_id):
        product = get_object_or_404(Product, product_id=product_id)
        order = get_object_or_404(Order, order_id=order_id)
        return order, product

    def check_order_permissions(self, request, order):
        """Check if the user is allowed to access/modify the order."""
        user = request.user
        if order.customer.user != user and not user.is_staff:
            raise PermissionDenied(
                "You do not have permission to access or modify this order."
            )

    def post(self, request, *args, **kwargs):
        # Extract order_id, product_id, and quantity from request data
        order_id = request.data.get("order_id")
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)  # Default quantity to 1

        # Ensure the quantity is valid
        if quantity < 1:
            return Response(
                {"error": "Quantity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order, product = self.get_order_and_product(order_id, product_id)

        # Check if the current user has permission to modify this order
        self.check_order_permissions(request, order)

        try:
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

        except ValidationError as e:
            # Handle validation errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemUpdateSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow staff to access all OrderItems, and regular users can access their own
        if self.request.user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__customer__user=self.request.user)

    def check_order_item_permissions(self, request, order_item):
        """Check if the user is allowed to access/modify/delete the order item."""
        user = request.user
        if order_item.order.customer.user != user and not user.is_staff:
            raise PermissionDenied(
                "You do not have permission to access this order item."
            )

    def get_object(self):
        """
        Retrieve the OrderItem object and check if the current user has the proper permissions.
        """
        order_id = self.kwargs["order_id"]
        item_id = self.kwargs["id"]

        # Get the order and order item
        order = get_object_or_404(Order, order_id=order_id)
        order_item = get_object_or_404(OrderItem, id=item_id, order=order)

        # Check if the current user has permission to access this order item
        self.check_order_item_permissions(self.request, order_item)

        return order_item

    def perform_update(self, serializer):
        """Handle the update of an order item."""
        order_item = self.get_object()

        # Ensure that the quantity is not less than 1
        if serializer.validated_data.get("quantity", order_item.quantity) < 1:
            return Response(
                {"error": "Quantity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        """Handle the deletion of an order item."""
        try:
            instance.delete()
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
