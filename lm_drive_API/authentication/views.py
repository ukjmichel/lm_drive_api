from rest_framework import generics, status
from rest_framework.exceptions import (
    NotFound,
    ValidationError,
    PermissionDenied as DRFValidationError,
)
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomTokenObtainPairSerializer, CustomerSerializer
from .permissions import IsCustomerOrAdmin


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Return queryset based on user's staff status
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Customer.objects.all()
            return Customer.objects.filter(user=self.request.user)
        return Customer.objects.none()

    def get(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().get(request, *args, **kwargs)

    def perform_create(self, serializer):
        user_data = serializer.validated_data.get("user", None)

        # Validation for user and username
        if user_data:
            username = user_data.get("username", None)
            if not username:
                raise DRFValidationError({"error": "Username is required."})

        # Proceed with creating the customer only if validation passes
        try:
            serializer.save()
        except Exception as e:
            # Catch any error during the save process and return a detailed response
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


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

    def _check_permissions(self, instance):
        """
        Vérifie si l'utilisateur connecté a les permissions nécessaires pour modifier ou supprimer un client.
        """
        if not self.request.user.is_staff and instance.user != self.request.user:
            raise PermissionDenied("Vous n'êtes pas autorisé à effectuer cette action.")

    def update(self, request, *args, **kwargs):
        """
        Met à jour les informations du client et de l'utilisateur associé.
        """
        instance = self.get_object()
        self._check_permissions(instance)  # Vérifie les permissions

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Sauvegarde des données via le sérialiseur
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        # Check if the serializer is valid, raise ValidationError if invalid
        if not serializer.is_valid():
            raise DRFValidationError(
                {"error": "Invalid credentials."}
            )  # Validation error example

        tokens = (
            serializer.validated_data
        )  # tokens will include access and refresh tokens
        return Response(tokens, status=status.HTTP_200_OK)
