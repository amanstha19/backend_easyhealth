from rest_framework.views import APIView
from rest_framework import permissions
from .serializers import ProductSerializer, UserSerializer, RegisterSerializer, OrderSerializer, \
    CustomTokenObtainPairSerializer, ServiceSerializer

from .models import Product, CustomUser, Cart, CartItem, Order, Booking, BookingReport
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
import logging
from rest_framework import viewsets
from django.http import HttpResponse
from django.views import View
from django.core.cache import cache
# Logging setup
logger = logging.getLogger(__name__)

@api_view(['GET'])
def getRoutes(request):
    return Response({'message': 'Hello from Django!'})

@api_view(['GET'])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, many=False)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return Response({'error': 'Product not found'}, status=404)

# Register new user
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate RefreshToken for the new user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "refresh": str(refresh),
            "access": str(access_token),
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
    try:
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )

        if not created:
            cart_item.quantity += 1

        # Handle prescription file upload if required
        if product.prescription_required:
            prescription_file = request.FILES.get('prescription')
            if prescription_file:
                cart_item.prescription_file = prescription_file

        cart_item.save()

        items = cart.cart_items.all()
        cart_items = [{
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.product.price),
            'total_item_price': float(item.product.price * item.quantity),
            'image': request.build_absolute_uri(item.product.image.url) if item.product.image else None,
        } for item in items]

        total_price = float(sum(item['total_item_price'] for item in cart_items))

        return Response({
            'cart_items': cart_items,
            'total_price': total_price
        }, status=200)

    except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found.")
        return Response({'error': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_cart(request, product_id):
    try:
        cart = Cart.objects.filter(user=request.user).first()

        # If cart doesn't exist, return empty response
        if not cart:
            return Response({
                'cart_items': [],
                'total_price': 0
            }, status=status.HTTP_200_OK)

        # Try to get the cart item
        cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()

        # If cart item doesn't exist, log it and return current cart state
        if not cart_item:
            logger.warning(
                f"Attempted to remove non-existent cart item. User: {request.user.id}, Product: {product_id}")
            items = cart.cart_items.all()
        else:
            # Delete the cart item if it exists
            cart_item.delete()
            items = cart.cart_items.all()

        # Get updated cart items
        cart_items = [{
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.product.price),
            'total_item_price': float(item.product.price * item.quantity),
            'image': request.build_absolute_uri(item.product.image.url) if item.product.image else None,
            'prescription': request.build_absolute_uri(item.prescription_file.url) if item.prescription_file else None
        } for item in items]

        total_price = float(sum(item['total_item_price'] for item in cart_items))

        return Response({
            'cart_items': cart_items,
            'total_price': total_price
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}", exc_info=True)
        return Response({
            'error': 'An error occurred while removing the item from cart'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# View cart
class ViewCart(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)
            items = cart.cart_items.all()

            if not items:
                return Response({'cart_items': []}, status=200)

            cart_items = [{
                'id': item.id,
                'product_id': item.product.id,
                'name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.product.price),
                'total_item_price': float(item.product.price * item.quantity),
                'image': request.build_absolute_uri(item.product.image.url) if item.product.image else None,
                'prescription': request.build_absolute_uri(item.prescription_file.url) if item.prescription_file else None
            } for item in items]

            total_price = float(sum(item['total_item_price'] for item in cart_items))

            return Response({
                'cart_items': cart_items,
                'total_price': total_price
            }, status=200)

        except Exception as e:
            logger.error(f"Error viewing cart: {e}")
            return Response({'error': 'Error viewing cart'}, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_cart_item_quantity(request, product_id):
    action = request.data.get('action')

    if action not in ['increase', 'decrease']:
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)

        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            return Response({"error": "Quantity cannot be decreased further."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.save()

        # Get all cart items for response
        items = cart.cart_items.all()
        cart_items = [{
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.product.price),
            'total_item_price': float(item.product.price * item.quantity),
            'image': request.build_absolute_uri(item.product.image.url) if item.product.image else None,
        } for item in items]

        total_price = float(sum(item['total_item_price'] for item in cart_items))

        return Response({
            'cart_items': cart_items,
            'total_price': total_price
        })

    except Cart.DoesNotExist:
        return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
    except CartItem.DoesNotExist:
        return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    try:
        cart = get_object_or_404(Cart, user=request.user)

        if cart.cart_items.count() == 0:
            return Response({'message': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum([item.product.price * item.quantity for item in cart.cart_items.all()])
        order = Order.objects.create(user=request.user, total_price=total_price, status="pending", address=request.data.get('address'))

        for cart_item in cart.cart_items.all():
            cart_item.order = order
            cart_item.save()

        # Clear the cart after creating the order
        cart.cart_items.all().delete()

        return Response({'message': 'Checkout complete, your cart is now empty.', 'order_id': order.id}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error during checkout: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

            with transaction.atomic():
                for item in cart_items:
                    product = get_object_or_404(Product, id=item['id'])
                    total_price += product.price * item['quantity']

                order = Order.objects.create(user=request.user, total_price=total_price, address=address)

                for item in cart_items:
                    product = get_object_or_404(Product, id=item['id'])
                    CartItem.objects.create(
                        product=product,
                        quantity=item['quantity'],
                        order=order
                    )

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


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
@api_view(['PATCH'])
def update_order_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    status = request.data.get('status')

    if status not in ['pending', 'shipped', 'delivered']:  # Example statuses
        return Response({"message": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

    order.status = status
    order.save()

    return Response({"message": "Order status updated successfully.", "order_id": order.id}, status=status.HTTP_200_OK)

 # Assuming this is the correct admin URL for bookings
# views.py
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from .models import Service, Booking, BookingReport
from .serializers import ServiceSerializer, BookingSerializer, BookingReportSerializer


class BookingCreateView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            # Check for duplicate bookings
            existing_booking = Booking.objects.filter(
                service=serializer.validated_data['service'],
                booking_date=serializer.validated_data['booking_date'],
                appointment_time=serializer.validated_data['appointment_time']
            ).exists()

            if existing_booking:
                return Response(
                    {'error': 'This time slot is already booked'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            booking = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingStatusView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        mobile_number = request.data.get('mobile_number')

        if not email or not mobile_number:
            return Response(
                {'error': 'Both email and mobile number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bookings = Booking.objects.filter(
            email=email,
            mobile_number=mobile_number
        ).order_by('-created_at')

        if not bookings:
            return Response(
                {'error': 'No bookings found with these details'},
                status=status.HTTP_404_NOT_FOUND
            )

        booking_data = []
        for booking in bookings:
            serializer = BookingSerializer(booking)
            reports = booking.reports.all()
            report_serializer = BookingReportSerializer(reports, many=True)

            booking_data.append({
                'booking': serializer.data,
                'reports': report_serializer.data
            })

        return Response(booking_data)


class ServiceListView(generics.ListCreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class ConfirmBookingView(views.APIView):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if booking.status != 'pending':
            return Response(
                {'error': f'Booking cannot be confirmed (current status: {booking.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'confirmed'
        booking.save()

        serializer = BookingSerializer(booking)
        return Response(serializer.data)


def confirm_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    # Add your logic for confirming the booking
    booking.status = 'confirmed'
    booking.save()
    return redirect('admin:app_booking_change', pk=booking.pk)


def cancel_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    # Add your logic for canceling the booking
    booking.status = 'canceled'
    booking.save()
    return redirect('admin:app_booking_change', pk=booking.pk)


def upload_report_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    # Add your logic for uploading a report
    return render(request, 'admin/upload_report.html', {'booking': booking})

import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Order, Payment
import json
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get("amount")

            if not amount:
                return JsonResponse({"error": "Amount is required"}, status=400)

            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency="usd",  # You can change the currency as per your requirement
            )

            return JsonResponse({"clientSecret": intent.client_secret})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
