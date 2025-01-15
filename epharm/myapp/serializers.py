from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Product, CustomUser, Cart, CartItem, Order

# User Serializer for creating and managing users (register)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    first_name = serializers.CharField(required=False, allow_blank=True)  # Optional first name
    last_name = serializers.CharField(required=False, allow_blank=True)   # Optional last name

    class Meta:
        model = CustomUser  # Use CustomUser model here
        fields = ['username', 'email', 'password', 'first_name', 'last_name']  # Specify fields
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Create user using the validated data
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),  # Use empty string if no first name
            last_name=validated_data.get('last_name', '')     # Use empty string if no last name
        )
        return user


# User Serializer (for listing user data)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser  # Ensure this is CustomUser if you're using it
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# User Serializer with Token (for including JWT token with user data)
class UserSerializerWithToken(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser  # Use CustomUser model
        fields = ['id', 'username', 'email', 'token', 'first_name', 'last_name']

    @staticmethod
    def get_token(obj: CustomUser) -> str:
        # Generate JWT access token for the user
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


# Custom Token Serializer (for login using email instead of username)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.EmailField(required=True)  # Use email instead of username

    def validate(self, attrs):
        # Custom validation logic can go here if needed
        return super().validate(attrs)


# Custom User Serializer for detailed profile data
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser  # Ensure this is your custom user model
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'city', 'country', 'phone']


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'prescription_required']


# CartItem Serializer
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']


# Cart Serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']


# Order Serializer (includes CartItem details for the order)
class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total_price', 'status', 'created_at']

    def get_items(self, obj):
        # Fetch related CartItems for the order
        cart_items = CartItem.objects.filter(order=obj)
        return CartItemSerializer(cart_items, many=True).data
