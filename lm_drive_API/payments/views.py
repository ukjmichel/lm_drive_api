from django.conf import settings
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.utils.timezone import now
from django.db import transaction
from .models import Order, Payment
from store.models import Stock
import stripe

# Set Stripe secret key from settings
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentIntentView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the order ID from the URL
        order_id = self.kwargs.get("order_id")

        # Fetch the order from the database
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            raise DRFValidationError({"order_id": "Order does not exist."})

        # Get the customer from the order
        customer = order.customer

        # Check if the customer has a Stripe customer ID
        if not customer.stripe_customer_id:
            try:
                # Create a new Stripe customer
                stripe_customer = stripe.Customer.create(
                    email=customer.email,
                    name=f"{customer.user.first_name} {customer.user.last_name}",
                )
                # Save the Stripe customer ID to the database
                customer.stripe_customer_id = stripe_customer["id"]
                customer.save()
            except stripe.error.StripeError as e:
                raise DRFValidationError(
                    {"error": f"Error creating Stripe customer: {str(e)}"}
                )

        # Get the payment method ID from the request body
        payment_method_id = request.data.get("payment_method_id")
        if not payment_method_id:
            raise DRFValidationError(
                {"payment_method_id": "Payment method ID is required."}
            )

        # Attach payment method to the Stripe customer if not already attached
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer.stripe_customer_id, type="card"
            )

            if not any(pm.id == payment_method_id for pm in payment_methods.data):
                stripe.PaymentMethod.attach(
                    payment_method_id, customer=customer.stripe_customer_id
                )
        except stripe.error.StripeError as e:
            raise DRFValidationError(
                {"error": f"Error attaching payment method: {str(e)}"}
            )

        # Create or confirm the PaymentIntent
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Amount in cents
                currency="eur",
                customer=customer.stripe_customer_id,
                payment_method=payment_method_id,
                off_session=False,
                confirm=True,
                setup_future_usage="off_session",
                return_url="http://localhost:5173/",
            )

            # Save the new payment in the database with "pending" status
            payment = Payment.objects.create(
                order=order,
                payment_method_id=payment_method_id,
                amount=order.total_amount,
                currency="eur",
                status="pending",
            )

            # Handle PaymentIntent status
            if payment_intent.status in ["requires_action", "requires_source_action"]:
                return Response(
                    {
                        "client_secret": payment_intent.client_secret,
                        "status": payment_intent.status,
                        "requires_action": True,
                    }
                )

            if payment_intent.status == "succeeded":
                payment.status = "succeeded"
                payment.save()
                Payment.objects.filter(order=order, status="pending").exclude(
                    id=payment.id
                ).delete()

            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "status": payment_intent.status,
                    "requires_action": False,
                }
            )
        except stripe.error.CardError as e:
            return Response({"error": f"Card error: {e.user_message}"}, status=400)
        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe error: {str(e)}"}, status=400)


class UpdatePaymentStatusView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the order ID and new status from the request body
        order_id = request.data.get("order_id")
        new_status = request.data.get("status")

        # Validate input data
        if not order_id or not new_status:
            raise DRFValidationError({"error": "Order ID and status are required."})

        if new_status not in ["succeeded", "failed"]:
            raise DRFValidationError(
                {"error": "Invalid status. Valid statuses are 'succeeded' or 'failed'."}
            )

        # Retrieve the associated order
        order = get_object_or_404(Order, order_id=order_id)

        # Get the last payment for this order
        last_payment = (
            Payment.objects.filter(order=order).order_by("-created_at").first()
        )

        if not last_payment:
            raise DRFValidationError({"error": "No payments found for this order."})

        # Update the status of the last payment
        last_payment.status = new_status
        last_payment.save()

        # Mark the order as fulfilled if the payment succeeded
        if new_status == "succeeded":
            self.mark_order_as_fulfilled(order)
            self.decrement_stock(order)

        # Return a success response with the updated payment information
        return Response(
            {
                "message": f"Payment status updated to {new_status} for order {order.order_id}.",
                "payment": {
                    "payment_id": last_payment.id,
                    "order_id": order.order_id,
                    "status": last_payment.status,
                    "amount": last_payment.amount,  # Assuming 'amount' is a field in the Payment model
                    "created_at": last_payment.created_at,
                },
                "order_status": order.status,  # Include updated order status
            },
            status=status.HTTP_200_OK,
        )

    def mark_order_as_fulfilled(self, order):
        """Mark the order as confirmed."""
        if order.status != "confirmed":
            order.status = "confirmed"
            order.fulfilled_date = now()
            order.save(update_fields=["status", "confirmed_date", "update_date"])

    def decrement_stock(self, order):
        """
        Decrement the stock for each product in the order.
        Uses the store related to the order instead of the request.
        """
        # Retrieve the store from the order
        store = order.store  # Accessing the store directly from the order
        if not store:
            raise DRFValidationError(
                {"error": "Store information is missing or invalid."}
            )

        # Iterate through the items in the order
        for (
            order_item
        ) in order.items.all():  # Assuming `order.items` is a related manager
            product_id = order_item.product.product_id
            quantity = order_item.quantity

            try:
                # Adjust stock atomically using the handle_payment_success method
                Stock.handle_payment_success(store.store_id, product_id, quantity)
            except DRFValidationError as e:
                raise DRFValidationError(
                    {
                        "error": f"Stock adjustment failed for product '{order_item.product.product_name}': {e.messages[0]}."
                    }
                )
            except Stock.DoesNotExist:
                raise DRFValidationError(
                    {
                        "error": f"Stock entry does not exist for product '{order_item.product.product_name}' in store '{store.name}'."
                    }
                )

        return {
            "success": True,
            "message": "Stock successfully decremented for the order.",
        }
