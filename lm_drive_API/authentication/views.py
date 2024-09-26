from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomTokenObtainPairSerializer, CustomerSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]  # Ensure only admin can access

    def get_queryset(self):
        # Only admins can see all customers
        return Customer.objects.all()

    def perform_create(self, serializer):
        # No need to associate with the user since only admins can create customers
        serializer.save()  # Save the new customer instance without user association


class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerOrAdmin]

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


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]  # Allow any user to access this view

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        return Response(tokens, status=status.HTTP_200_OK)
