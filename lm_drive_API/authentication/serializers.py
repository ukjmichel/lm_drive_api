from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model to include username and email.
    """

    password = serializers.CharField(
        write_only=True
    )  # Add password field for user creation

    class Meta:
        model = User
        fields = [
            "username",
            "password",
        ]  # Expose username, email, and password fields

    def create(self, validated_data):
        password = validated_data.pop("password")  # Extract password
        user = User(**validated_data)  # Create user instance without saving yet
        user.set_password(password)  # Set password
        user.save()  # Now save the user
        return user


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested serializer to create a user

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "user",  # Exposes the nested user data (username, email)
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "postal_code",
        ]
        read_only_fields = ["customer_id"]  # customer_id is read-only

    def create(self, validated_data):
        user_data = validated_data.pop("user")  # Extract user data

        # Ensure password is provided
        if "password" not in user_data:
            raise serializers.ValidationError({"password": "This field is required."})

        email = user_data.get("email")

        # Check if a user with this email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        # Create the User instance using the nested serializer
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)  # Validate user data
        user = user_serializer.save()  # Create user

        # Create the Customer instance linked to the User
        customer = Customer.objects.create(user=user, **validated_data)

        return customer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        return token
