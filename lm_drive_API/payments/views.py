import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .models import Order

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
            raise ValidationError({"order_id": "Order does not exist."})

        # Get customer_id from the order
        customer_id = order.customer.stripe_customer_id

        if not customer_id:
            raise ValidationError(
                {"customer_id": "Customer does not have a Stripe customer ID."}
            )

        # Get the payment method ID from the request body
        payment_method_id = request.data.get("payment_method_id")
        if not payment_method_id:
            raise ValidationError(
                {"payment_method_id": "Payment method ID is required."}
            )

        # Retrieve the customer object from Stripe
        try:
            customer = stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            raise ValidationError({"error": f"Error retrieving customer: {str(e)}"})

        # Check if the payment method is already attached to the customer
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card",  # Assuming we're dealing with card payment methods
        )

        # If payment method is not already attached, attach it
        if not any(pm.id == payment_method_id for pm in payment_methods.data):
            try:
                stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            except stripe.error.StripeError as e:
                raise ValidationError(
                    {"error": f"Error attaching payment method: {str(e)}"}
                )

        # Create or confirm PaymentIntent with the associated customer and payment method
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Amount in cents
                currency="eur",  # Currency in ISO format
                customer=customer_id,  # Customer ID in Stripe
                payment_method=payment_method_id,  # The payment method ID
                off_session=False,  # Indicating that the payment is off-session
                confirm=True,  # Auto-confirm the PaymentIntent
                setup_future_usage="off_session",  # Optional: Save for future payments if needed
                return_url="http://localhost:5173/",  # Add your return URL
            )

            # Check if the payment requires further authentication (e.g., 3D Secure)
            if (
                payment_intent.status == "requires_action"
                or payment_intent.status == "requires_source_action"
            ):
                return Response(
                    {
                        "client_secret": payment_intent.client_secret,
                        "status": payment_intent.status,
                        "requires_action": True,
                    }
                )

            # If the payment is successful or does not require further action (no 3D Secure needed)
            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "status": payment_intent.status,
                    "requires_action": False,
                }
            )

        except stripe.error.CardError as e:
            # Handle card-related errors separately for better feedback
            return Response(
                {"error": f"Card error: {e.user_message}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as e:
            # Generic Stripe error handler
            return Response(
                {"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )


class StripeWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        # Retrieve the Stripe signature header and payload from the request
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = (
            settings.STRIPE_ENDPOINT_SECRET
        )  # Your Stripe webhook secret key

        # Verify the webhook signature to ensure it is coming from Stripe
        try:
            # Use Stripe's helper method to verify the signature
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            return Response(
                {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(
                {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Now, handle the event (event['type'] gives you the event type)
        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            # Handle successful payment
            payment_intent = event_data
            # Implement your logic, e.g., update the order status to 'paid'
            print(f"PaymentIntent {payment_intent['id']} succeeded.")

        elif event_type == "payment_intent.payment_failed":
            # Handle failed payment
            payment_intent = event_data
            # Implement your logic, e.g., notify user about the failure
            print(f"PaymentIntent {payment_intent['id']} failed.")

        # Add other event types here as needed (like `invoice.payment_succeeded`)

        # Return a success response to Stripe to acknowledge receipt of the event
        return Response({"status": "success"}, status=status.HTTP_200_OK)
