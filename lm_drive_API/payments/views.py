from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Payment
from .serializers import PaymentSerializer
import stripe
from django.conf import settings
from orders.models import Order

# Set your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(["POST"])
def process_payment(request):
    print(f"Request data: {request.data}")  # Log the incoming request data
    serializer = PaymentSerializer(data=request.data)

    if serializer.is_valid():
        try:
            order_id = serializer.validated_data["order_id"]
            order = Order.objects.get(order_id=order_id)  # Fetch order using order_id
            payment_method_id = serializer.validated_data["payment_method_id"]
            amount = serializer.validated_data["amount"]
            currency = serializer.validated_data["currency"]

            # Get customer from the order instance
            customer = order.customer
            stripe_customer_id = (
                customer.stripe_customer_id
            )  # Get the local customer ID
            print(f"Current customer ID: {stripe_customer_id}")

            # Check if Stripe customer ID exists
            if not stripe_customer_id:
                # Create a new Stripe customer
                stripe_customer = stripe.Customer.create(email=customer.email)
                customer.customer_id = stripe_customer["id"]
                customer.save()  # Save the new Stripe customer ID
                stripe_customer_id = stripe_customer["id"]
                print(f"Created new Stripe customer: {stripe_customer_id}")

            # Attach the Payment Method to the Customer
            stripe.PaymentMethod.attach(payment_method_id, customer=stripe_customer_id)
            print(f"Payment method {payment_method_id} attached successfully")

            # Create a PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency=currency,
                payment_method=payment_method_id,
                customer=stripe_customer_id,  # Attach the customer to the PaymentIntent
                confirm=True,  # Immediately confirm the payment
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
            )
            print(f"Payment intent created successfully: {intent}")

            # Save payment information after successful Stripe transaction
            Payment.objects.create(
                order=order,
                payment_method_id=payment_method_id,
                amount=amount,
                currency=currency,
            )

            # Return success response with payment details
            return Response(
                {
                    "status": "success",  # Added status key
                    "message": "Payment successful",
                    "payment": serializer.data,
                    "payment_intent": intent,
                },
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.CardError as e:
            return Response(
                {"status": "error", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.StripeError as e:
            return Response(
                {"status": "error", "error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "error": f"Payment processing failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    print(f"Serializer errors: {serializer.errors}")
    return Response(
        {"status": "error", "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )
