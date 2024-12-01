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

    def update(self, instance, validated_data):
        """
        Met à jour un utilisateur, y compris le mot de passe s'il est fourni.
        """
        password = validated_data.pop("password", None)
        instance.username = validated_data.get("username", instance.username)
        if password:
            instance.set_password(password)  # Hash le mot de passe
        instance.save()  # Sauvegarde l'utilisateur
        return instance  # Retourne l'instance mise à jour


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
        """
        Met à jour un client et les données utilisateur associées.
        """
        user_data = validated_data.pop("user", None)

        # Mise à jour des données utilisateur imbriquées
        if user_data:
            user_instance = instance.user
            user_serializer = UserSerializer(
                user_instance, data=user_data, partial=True
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()  # Appelle la méthode update de UserSerializer

        # Mise à jour uniquement des champs modifiés pour le client
        for attr, value in validated_data.items():
            if getattr(instance, attr) != value:
                setattr(instance, attr, value)
        instance.save()

        return instance  # Retourne l'instance mise à jour


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
