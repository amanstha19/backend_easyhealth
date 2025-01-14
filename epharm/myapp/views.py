from rest_framework.views import APIView
from rest_framework import permissions
import logging
from .serializers import ProductSerializer, UserSerializer, RegisterSerializer, OrderSerializer
from .models import Product, CustomUser, Cart, CartItem, Order
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction

# Logging setup
logger = logging.getLogger(__name__)

# Get all available routes
@api_view(['GET'])
def getRoutes(request):
    return Response({'message': 'Hello from Django!'})

# Get all products
@api_view(['GET'])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

# Get a specific product by ID
@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, many=False)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return Response({'error': 'Product not found'}, status=404)

# Get user profile (protected route)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    logger.debug(f"User data: {user.username}, {user.email}, {user.first_name}, {user.last_name}")
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

# Register new user
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate RefreshToken for the new user
        refresh = RefreshToken.for_user(user)

        # Access the access_token from the RefreshToken instance
        access_token = refresh.access_token

        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "refresh": str(refresh),
            "access": str(access_token),  # Use the access_token
        }, status=status.HTTP_201_CREATED)

# Custom Login API View to handle login and token generation
class CustomLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        logger.debug("Request Body:", request.data)
        return super().post(request, *args, **kwargs)

# Check if an email is already in use
@csrf_exempt
def check_email(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            email = body.get('email', None)

            if email is None:
                return JsonResponse({'error': 'Email is required.'}, status=400)

            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email is already in use.'}, status=409)

            return JsonResponse({'message': 'Email is available.'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

# View to get the user's profile information
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

# Add product to the cart
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Get or create a cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Check if the item is already in the cart
    cart_item, created = CartItem.objects.get_or_create(product=product, cart=cart, defaults={'quantity': 1})

    if not created:  # If the item is already in the cart, increase the quantity
        cart_item.quantity += 1
        cart_item.save()

    # Add the item to the cart
    cart.items.add(cart_item)

    return Response({'message': 'Item added to cart', 'cart_item_id': cart_item.id}, status=status.HTTP_200_OK)

# Remove product from the cart
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)

    try:
        cart_item = get_object_or_404(CartItem, product_id=product_id, cart=cart)
        cart.items.remove(cart_item)  # Remove item from the cart

        # Check if there are no other instances of this cart_item in the cart
        if cart.items.filter(id=cart_item.id).count() == 0:
            cart_item.delete()  # Delete cart item if no other reference exists

        return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)

# View cart and calculate total price
class ViewCart(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.all()

        if not items:
            return Response({'message': 'Your cart is empty'}, status=status.HTTP_200_OK)

        total_price = sum(item.product.price * item.quantity for item in items)
        cart_data = [{'product_name': item.product.name, 'quantity': item.quantity, 'price': item.product.price,
                      'total_item_price': item.product.price * item.quantity} for item in items]

        return Response({'cart': cart_data, 'total_price': total_price}, status=status.HTTP_200_OK)

# Proceed with checkout (clear cart)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    # Process checkout logic (e.g., creating an order)
    # For now, we'll just clear the cart
    cart.items.clear()

    return Response({'message': 'Checkout complete, your cart is now empty.'}, status=status.HTTP_200_OK)

class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            cart_items_data = request.data.get('cart_items')
            address = request.data.get('address')
            prescription = request.data.get('prescription', None)

            if not cart_items_data or not address:
                return Response({"detail": "Missing cart items or address."}, status=status.HTTP_400_BAD_REQUEST)

            cart_items = json.loads(cart_items_data)
            total_price = 0

            # Start a database transaction
            with transaction.atomic():
                # Calculate total price and create the order object
                for item in cart_items:
                    product = Product.objects.get(id=item['id'])
                    total_price += product.price * item['quantity']

                order = Order.objects.create(user=request.user, total_price=total_price, address=address)

                # Process cart items and add them to the order
                for item in cart_items:
                    product = Product.objects.get(id=item['id'])
                    CartItem.objects.create(
                        product=product,
                        quantity=item['quantity'],
                        order=order  # Correctly associate CartItem with Order
                    )

                # Handle prescription file upload if provided
                if prescription:
                    prescription_file = request.FILES.get('prescription')
                    if prescription_file:
                        order.prescription = prescription_file
                        order.save()

                return Response({"order_id": order.id}, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
