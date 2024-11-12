from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Password is write-only

    class Meta:
        model = User
        fields = ["username", "password"]

    def validate_username(self, value):
        """Custom username validation"""
        if len(value) < 4:
            raise serializers.ValidationError(
                "Username must be at least 4 characters long."
            )
        if len(value) > 20:
            raise serializers.ValidationError(
                "Username cannot be more than 20 characters long."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        """Create a new user instance"""
        password = validated_data.pop("password")  # Extract password
        user = User(**validated_data)  # Create user instance
        user.set_password(password)  # Set password (hashed)
        user.save()  # Save the user
        return user


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested UserSerializer for user data
    stripe_customer_id = serializers.CharField(
        read_only=True
    )  # Read-only field for stripe_customer_id

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "user",
            "email",
            "stripe_customer_id",  # Include Stripe ID only for staff
        ]
        read_only_fields = [
            "customer_id",
            "stripe_customer_id",
        ]  # Make these fields read-only

    def validate_email(self, value):
        """Validate that the email does not already exist for a customer"""
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A customer with this email already exists."
            )
        return value

    def create(self, validated_data):
        """Create a new customer instance"""
        user_data = validated_data.pop("user")  # Extract user data from validated data

        # Ensure password is provided for user creation
        if "password" not in user_data:
            raise serializers.ValidationError({"password": "This field is required."})

        # Create the user instance using the nested UserSerializer
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)  # Validate the user data
        user = user_serializer.save()  # Create the user

        # Create the Customer instance and link it to the created user
        customer = Customer.objects.create(user=user, email=validated_data["email"])

        return customer

    def update(self, instance, validated_data):
        """Update an existing customer instance"""
        user_data = validated_data.pop("user", None)  # Extract user data, if provided
        user = (
            instance.user
        )  # Get the current user instance associated with the customer

        # Update the User fields if user data is provided
        if user_data:
            username = user_data.get("username", user.username)
            if "password" in user_data:
                user.set_password(user_data["password"])  # Update password if provided
            user.username = username  # Update username if provided
            user.save()

        # Update the Customer fields
        instance.email = validated_data.get("email", instance.email)
        instance.save()

        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the token
        token["username"] = user.username
        token["is_admin"] = user.is_superuser  # Assuming is_superuser means admin
        token["is_staff"] = user.is_staff  # Optional: add is_staff if needed

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra responses here if needed, for example, including user info in the response
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "is_admin": self.user.is_superuser,
            "is_staff": self.user.is_staff,
        }
        return data
