from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model to include username and password.
    """

    password = serializers.CharField(
        write_only=True
    )  # Add password field for user creation

    class Meta:
        model = User
        fields = ["username", "password"]  # Expose username and password fields

    def create(self, validated_data):
        password = validated_data.pop("password")  # Extract password
        user = User(**validated_data)  # Create user instance without saving yet
        user.set_password(password)  # Set password
        user.save()  # Save the user
        return user


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested serializer to create/update a user

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "user",
            "email",
        ]  # Expose the nested user data and email
        read_only_fields = ["customer_id"]  # customer_id is read-only

    def create(self, validated_data):
        user_data = validated_data.pop("user")  # Extract user data

        # Ensure password is provided
        if "password" not in user_data:
            raise serializers.ValidationError({"password": "This field is required."})

        email = validated_data.get("email")  # Get email from validated data

        # Check if a user with this username already exists
        if User.objects.filter(username=user_data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "A user with this username already exists."}
            )

        # Check if a customer with this email already exists
        if Customer.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A customer with this email already exists."}
            )

        # Create the User instance using the nested serializer
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)  # Validate user data
        user = user_serializer.save()  # Create user

        # Create the Customer instance linked to the User, passing the email
        customer = Customer.objects.create(user=user, email=email)

        return customer

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)  # Extract user data, if provided
        user = (
            instance.user
        )  # Get the current user instance associated with the customer

        # Update the User fields if user data is present
        if user_data:
            user.username = user_data.get("username", user.username)  # Update username
            if "password" in user_data:
                user.set_password(user_data["password"])  # Update password
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
