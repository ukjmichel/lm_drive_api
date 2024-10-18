from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomTokenObtainPairSerializer, CustomerSerializer
from .permissions import IsCustomerOrAdmin


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [
        AllowAny
    ]  # Allow access to any user, including unauthenticated users

    def perform_create(self, serializer):
        serializer.save()


class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsCustomerOrAdmin]

    def get_queryset(self):
        # Allow admin to see all customers, regular users see their own customers
        if self.request.user.is_staff:  # Check if the user is an admin
            return Customer.objects.all()  # Admins can see all customers
        return Customer.objects.filter(
            user=self.request.user
        )  # Regular users see their own customers

    def get_object(self):
        customer_id = self.kwargs.get("customer_id")  # Capture customer_id from URL
        try:
            customer = self.get_queryset().get(
                customer_id=customer_id
            )  # Get customer filtered by user
            return customer
        except Customer.DoesNotExist:
            raise NotFound(detail="Customer not found.")

    def get_serializer(self, *args, **kwargs):
        # Use the super method to get the serializer
        serializer = super().get_serializer(*args, **kwargs)

        # If the user is not a staff member, exclude the stripe_customer_id
        if not self.request.user.is_staff:
            serializer.fields.pop("stripe_customer_id", None)

        return serializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = (
            serializer.validated_data
        )  # tokens will include access and refresh tokens

        return Response(tokens, status=status.HTTP_200_OK)
    