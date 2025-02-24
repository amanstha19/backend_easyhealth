
from rest_framework import permissions
from .serializers import ProductSerializer, RegisterSerializer, OrderSerializer, CustomTokenObtainPairSerializer

from .models import  CustomUser, Cart, CartItem, Order
from django.shortcuts import redirect, render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import api_view, permission_classes

from django.views.decorators.csrf import csrf_exempt

from django.db import transaction


import json

from django.http import JsonResponse

from rest_framework import generics, views

from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Service
from .serializers import ServiceSerializer, BookingSerializer, BookingReportSerializer
from django.db.models import Q


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, userPayment,Product
import hmac
import hashlib
import base64
import logging
import time

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
                "last_name": user.last_name,
                "city": user.city,
                "country": user.country,
                "phone": user.phone
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

                    # Check if there is enough stock
                    if product.stock < item['quantity']:
                        return Response({"detail": f"Not enough stock for {product.name}."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    total_price += product.price * item['quantity']
                    # Decrease stock
                    product.stock -= item['quantity']
                    product.save()

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



class ProcessPaymentView(APIView):
    def post(self, request):
        try:
            if 'data' in request.data or 'status' in request.data:
                transaction_uuid = request.data.get('transaction_uuid')
                status_code = request.data.get('status', 'SUCCESS')  # Default to SUCCESS if data present
                transaction_code = request.data.get('transaction_code')

                try:
                    payment = userPayment.objects.get(transaction_uuid=transaction_uuid)
                    payment.transaction_code = transaction_code
                    payment.status = status_code
                    payment.save()

                    logger.info(f"Payment callback processed successfully for transaction {transaction_uuid}")
                    return Response({
                        "message": "Payment successful",
                        "transaction_uuid": transaction_uuid
                    }, status=status.HTTP_200_OK)

                except userPayment.DoesNotExist:
                    logger.error(f"Payment not found for transaction {transaction_uuid}")
                    return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

            amount = float(request.data.get('amount', 0))
            tax_amount = float(request.data.get('tax_amount', 0))
            transaction_uuid = request.data.get('transaction_uuid')

            if not transaction_uuid:
                return Response({"error": "Missing transaction_uuid"}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = amount + tax_amount

            payment = userPayment.objects.create(
                amount=amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                transaction_uuid=transaction_uuid,
                status="PENDING",
                user=request.user,
            )

            message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code=EPAYTEST"
            secret_key = "8gBm/:&EnhH.1/q"
            signature = base64.b64encode(
                hmac.new(
                    secret_key.encode(),
                    message.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()

            user_payment_data = {
                "amount": str(amount),
                "tax_amount": str(tax_amount),
                "total_amount": str(total_amount),
                "transaction_uuid": transaction_uuid,
                "product_code": "EPAYTEST",
                "product_service_charge": "0",
                "product_delivery_charge": "0",
                "success_url": f"https://developer.esewa.com.np/success/",  # eSewa success URL
                "failure_url": f"https://developer.esewa.com.np/failure/",  # eSewa failure URL
                "signed_field_names": "total_amount,transaction_uuid,product_code",
                "signature": signature
            }

            return Response(user_payment_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def process_payment_callback(self, request):
        """Handle the callback and add a delay before redirecting"""
        try:
            # Introduce a 10-second delay
            time.sleep(10)

            # Get the status and transaction data from the query params
            status = request.GET.get('status', 'FAILED')
            transaction_data = request.GET.get('data', '')

            # Construct the frontend URL with payment status
            payment_status_url = f"http://localhost:5173/payment-success?status={status}&data={transaction_data}"

            # Return the URL as a JSON response
            return JsonResponse({"redirect_url": payment_status_url})

        except Exception as e:
            logger.error(f"Error in process_payment_callback: {str(e)}")
            return JsonResponse({"error": "Failed to process payment callback"}, status=status.HTTP_400_BAD_REQUEST)

class PaymentSuccessView(APIView):
    def get(self, request):
        return Response({"message": "Payment was successful!"}, status=status.HTTP_200_OK)

class PaymentFailureView(APIView):
    def get(self, request):
        return Response({"message": "Payment failed. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

class test:
    pass



from .models import Product



class ProductSearchAPIView(APIView):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '').strip()
        category = request.GET.get('category', '').strip()

        # Basic query for filtering by name and description (case-insensitive)
        filters = Q(name__icontains=search_query) | Q(description__icontains=search_query)

        # Apply category filter if provided
        if category:
            filters &= Q(category=category)

        # Get products with applied filters
        products = Product.objects.filter(filters)

        # Serialize and return the products
        product_data = [{
            "id": product.id,
            "name": product.name,
            "generic_name": product.generic_name,
            "category": product.category,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "prescription_required": product.prescription_required,
            "image": product.image.url if product.image else None,
        } for product in products]

        return Response(product_data, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            # Get the user's profile information
            user_data = {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }

            # Fetch the user's orders and related cart items
            orders = Order.objects.filter(user=request.user)
            orders_data = []

            for order in orders:
                cart_items = CartItem.objects.filter(order=order)
                cart_items_data = [
                    {
                        'product_id': item.product.id,
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'total_price': item.product.price * item.quantity
                    } for item in cart_items
                ]
                order_data = {
                    'order_id': order.id,
                    'total_price': order.total_price,
                    'status': order.status,
                    'address': order.address,
                    'cart_items': cart_items_data,
                }
                orders_data.append(order_data)

            # Add orders to the response
            user_data['orders'] = orders_data

            return Response(user_data)

        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return Response({"detail": "Error fetching profile data."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class BookingPaymentView(APIView):
    def post(self, request):
        try:
            # Handle payment callback
            if 'data' in request.data or 'status' in request.data:
                transaction_uuid = request.data.get('transaction_uuid')
                status_code = request.data.get('status', 'SUCCESS')
                transaction_code = request.data.get('transaction_code')

                try:
                    payment = userPayment.objects.get(transaction_uuid=transaction_uuid)
                    payment.transaction_code = transaction_code
                    payment.status = status_code
                    payment.save()

                    # Update booking status if payment is successful
                    if status_code == 'SUCCESS' and payment.booking:
                        booking = payment.booking
                        booking.status = 'confirmed'
                        booking.save()

                    logger.info(f"Booking payment callback processed successfully for transaction {transaction_uuid}")
                    return Response({
                        "message": "Payment successful",
                        "transaction_uuid": transaction_uuid
                    }, status=status.HTTP_200_OK)

                except userPayment.DoesNotExist:
                    logger.error(f"Payment not found for transaction {transaction_uuid}")
                    return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

            # Initialize new payment
            booking_id = request.data.get('booking_id')
            amount = float(request.data.get('amount', 0))
            tax_amount = float(request.data.get('tax_amount', 0))
            transaction_uuid = request.data.get('transaction_uuid')

            if not transaction_uuid or not booking_id:
                return Response({"error": "Missing transaction_uuid or booking_id"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                booking = Booking.objects.get(id=booking_id)
            except Booking.DoesNotExist:
                return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

            total_amount = amount + tax_amount

            # Create payment record
            payment = userPayment.objects.create(
                amount=amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                transaction_uuid=transaction_uuid,
                status="PENDING",
                user=request.user if request.user.is_authenticated else None,
                booking=booking
            )

            # Generate eSewa payment signature
            message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code=EPAYTEST"
            secret_key = "8gBm/:&EnhH.1/q"  # eSewa test secret key
            signature = base64.b64encode(
                hmac.new(
                    secret_key.encode(),
                    message.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()

            # Prepare eSewa payment data
            payment_data = {
                "amount": str(amount),
                "tax_amount": str(tax_amount),
                "total_amount": str(total_amount),
                "transaction_uuid": transaction_uuid,
                "product_code": "EPAYTEST",
                "product_service_charge": "0",
                "product_delivery_charge": "0",
                "success_url": f"https://developer.esewa.com.np/success/",  # Update with your success URL
                "failure_url": f"https://developer.esewa.com.np/failure/",  # Update with your failure URL
                "signed_field_names": "total_amount,transaction_uuid,product_code",
                "signature": signature
            }

            return Response(payment_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Booking payment processing error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def process_payment_callback(self, request):
        try:
            time.sleep(10)  # Add delay for payment processing
            status = request.GET.get('status', 'FAILED')
            transaction_data = request.GET.get('data', '')

            payment_status_url = f"http://localhost:5173/booking-payment-success?status={status}&data={transaction_data}"

            return JsonResponse({"redirect_url": payment_status_url})
        except Exception as e:
            logger.error(f"Error in process_payment_callback: {str(e)}")
            return JsonResponse({"error": "Failed to process payment callback"}, status=status.HTTP_400_BAD_REQUEST)



