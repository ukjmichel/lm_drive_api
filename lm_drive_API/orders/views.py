from decimal import Decimal
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response

from lm_drive_API import settings
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
)
from authentication.models import Customer
from store.models import Product, Store
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML


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
        items_data = self.request.data.get("items", [])
        customer_id = self.request.data.get("customer_id")
        store_id = self.request.data.get("store_id")

        if not customer_id or not store_id:
            raise DRFValidationError("'customer_id' and 'store_id' are required.")

        customer = get_object_or_404(Customer, customer_id=customer_id)
        store = get_object_or_404(Store, store_id=store_id)

        # Ensure only one pending order per customer
        if Order.objects.filter(customer=customer, status="pending").exists():
            raise DRFValidationError(
                "Only one pending order can be created per customer."
            )

        with transaction.atomic():
            order = serializer.save(customer=customer, store=store)
            total_ht, total_ttc = 0, 0

            for item_data in items_data:
                product = get_object_or_404(Product, product_id=item_data["product_id"])
                quantity = int(item_data.get("quantity", 1))
                if quantity < 1:
                    raise DRFValidationError("Quantity must be at least 1.")

                price_ht = product.price_ht
                tva = product.tva
                price_ttc = round(price_ht * (1 + tva / 100), 2)
                total_ht += price_ht * quantity
                total_ttc += price_ttc * quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price_ht=price_ht,
                    tva=tva,
                    price_ttc=price_ttc,
                    quantity=quantity,
                    total_ht=price_ht * quantity,
                    total_ttc=price_ttc * quantity,
                )

            # Update order totals
            order.total_ht = total_ht
            order.total_ttc = total_ttc
            order.save()


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related("customer", "store").prefetch_related(
        "items"
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer__user=user)

    def perform_update(self, serializer):
        order = self.get_object()
        new_status = serializer.validated_data.get("status")
        user = self.request.user

        # Restrict non-staff users from updating certain statuses
        if not user.is_staff:
            if order.customer.user != user:
                raise PermissionDenied(
                    "You do not have permission to update this order."
                )
            if order.status in ["confirmed", "ready", "fulfilled"]:
                raise DRFValidationError("You cannot update an order with this status.")

        with transaction.atomic():
            if new_status == "confirmed" and order.status != "confirmed":
                serializer.save(confirmed_date=now())
            elif new_status == "fulfilled" and order.status != "fulfilled":
                serializer.save(fulfilled_date=now())
            else:
                serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff can delete orders.")
        instance.delete()


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
            defaults={"quantity": quantity, "price_ttc": product.price_ttc},
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


class GenerateInvoiceView(views.APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view.

    def get(self, request, order_id):
        # Récupérer la commande
        order = get_object_or_404(Order, order_id=order_id)

        # Calculer la TVA
        total_tva = Decimal(order.total_ttc) - Decimal(order.total_ht)

        # Rendre le contenu HTML
        try:
            html_content = render_to_string(
                "invoice_template.html",
                {
                    "order": order,
                    "total_tva": total_tva,  # Passer la TVA au template
                    "now": now(), 
                },
            )
        except Exception as e:
            return Response(
                {"error": f"Error rendering invoice template: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Localiser le fichier CSS
        css_path = os.path.join(settings.BASE_DIR, "orders/templates/invoice.css")
        if not os.path.exists(css_path):
            return Response(
                {"error": f"CSS file not found: {css_path}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Générer le PDF avec le CSS
        try:
            pdf = HTML(string=html_content).write_pdf(stylesheets=[css_path])
        except Exception as e:
            return Response(
                {"error": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Retourner la réponse
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="facture_{order.order_id}.pdf"'
        )
        return response


