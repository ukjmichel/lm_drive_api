from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework.exceptions import NotFound


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        return super().get(
            request, *args, **kwargs
        )  # Handle GET request for listing customers

    def post(self, request, *args, **kwargs):
        return super().post(
            request, *args, **kwargs
        )  # Handle POST request for creating a customer

    def perform_create(self, serializer):
        """Override this method to customize the creation process if needed."""
        serializer.save()  # Default behavior: Save the new customer instance


class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        customer_id = self.kwargs.get("customer_id")  # Capture customer_id from URL
        try:
            return Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            raise NotFound(detail="Customer not found.")
