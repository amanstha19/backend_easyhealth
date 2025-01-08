from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Product
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
User = get_user_model()

# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


# User Serializer for creating and managing users (register)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # Create user using the validated data
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


# User Serializer (for listing user data)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


# User Serializer with Token (for including JWT token with user data)
class UserSerializerWithToken(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'token']

    @staticmethod
    def get_token(obj: User) -> str:
        # Generate JWT access token for the user
        token = RefreshToken.for_user(obj)
        return str(token.access_token)



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.EmailField(required=True)  # Use email instead of username

    def validate(self, attrs):
        # Custom validation logic can go here if needed
        return super().validate(attrs)