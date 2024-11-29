from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
)
from authentication.models import Customer
from store.models import Product, Store


# Order List and Create View
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer = Customer.objects.filter(user=user).first()
        return (
            Order.objects.filter(customer=customer)
            if customer
            else Order.objects.none()
        )

    def perform_create(self, serializer):
        user = self.request.user
        items = self.request.data.get("items", [])
        customer_id = self.request.data.get("customer_id")
        store_id = self.request.data.get("store_id")

        if not customer_id or not store_id:
            raise DRFValidationError("'customer_id' and 'store_id' are required.")

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            raise DRFValidationError(f"Customer with id {customer_id} does not exist.")

        try:
            store = Store.objects.get(store_id=store_id)
        except Store.DoesNotExist:
            raise DRFValidationError(f"Store with id {store_id} does not exist.")

        # Check if there's already a pending order for this customer
        if Order.objects.filter(customer=customer, status="pending").exists():
            raise DRFValidationError(
                "Only one pending order can be created per customer."
            )

        # Save the order first to generate the order_id
        order = serializer.save(customer=customer, store=store)

        total_amount = 0
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)

            if int(quantity) < 1:
                raise DRFValidationError("Quantity must be at least 1.")

            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                raise DRFValidationError(
                    f"Product with id {product_id} does not exist."
                )

            price = product.price
            total_price = price * int(quantity)

            # Create the order item
            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=quantity,
                total=total_price,
            )

            total_amount += total_price

        # Update the order's total amount after all items are added
        order.total_amount = total_amount
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# Order Retrieve, Update, and Delete View
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related("customer", "customer__user").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.select_related("customer", "customer__user").all()
        return Order.objects.filter(customer__user=user).select_related("customer")

    def perform_update(self, serializer):
        order = self.get_object()
        new_status = serializer.validated_data.get("status")
        user = self.request.user

        # Restrict status updates to "ready" or "fulfilled" for staff only
        if new_status in ["ready", "fulfilled"] and not user.is_staff:
            raise PermissionDenied(
                {
                    "detail": "Only staff or admin users can update the status to 'ready' or 'fulfilled'."
                }
            )

        # Non-staff users can only update their own orders and limited statuses
        if not user.is_staff:
            if order.customer.user != user:
                raise PermissionDenied(
                    {"detail": "You do not have permission to update this order."}
                )
            if order.status in ["confirmed", "ready", "fulfilled"]:
                raise DRFValidationError(
                    {
                        "status": [
                            f"You cannot update an order that is already {order.status}."
                        ]
                    }
                )
            if new_status and new_status != "confirmed":
                raise DRFValidationError(
                    {"status": ["Only 'confirmed' status is allowed for your role."]}
                )

        # Save the serializer to persist changes
        updated_instance = serializer.save()

        # Return the updated instance (or other details) as feedback
        return {
            "message": "Order updated successfully",
            "order_id": updated_instance.order_id,
            "status": updated_instance.status,
        }

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied({"detail": "Only staff can delete orders."})
        try:
            instance.delete()
        except Exception as e:
            raise DRFValidationError({"detail": f"Error deleting order: {str(e)}"})


# Add Item to Order View
class AddOrderItemView(generics.CreateAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if int(quantity) < 1:
            return Response(
                {"error": "Quantity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, order_id=order_id)
        product = get_object_or_404(Product, product_id=product_id)

        if order.customer.user != request.user and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to modify this order.")

        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"quantity": quantity, "price": product.price},
        )
        if not created:
            order_item.quantity += quantity
            order_item.save()

        return Response(
            OrderItemSerializer(order_item).data, status=status.HTTP_201_CREATED
        )


# Order Item Retrieve, Update, and Delete View
class OrderItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__customer__user=user)

    def perform_update(self, serializer):
        order_item = self.get_object()
        new_quantity = serializer.validated_data.get("quantity", order_item.quantity)
        if int(new_quantity) < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        serializer.save()

    def perform_destroy(self, instance):
        if (
            self.request.user.is_staff
            or instance.order.customer.user == self.request.user
        ):
            instance.delete()
        else:
            raise PermissionDenied(
                "You do not have permission to delete this order item."
            )
