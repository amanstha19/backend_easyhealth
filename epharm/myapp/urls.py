
# myapp/urls.py (App-level URLs)
from django.urls import path
from . import views
from .views import (
    CustomLoginAPIView,
    UserProfileView,
    PlaceOrderView,
    update_cart_item_quantity,
    update_order_status,
    ConfirmBookingView,
    BookingCreateView,
    BookingStatusView,
    ServiceListView,
    ServiceDetailView,
    OrderDetailView,
    ViewCart,
    RegisterAPIView, create_payment_intent,

)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = 'myapp'

urlpatterns = [
    # Base Routes
    path('', views.getRoutes, name='getRoutes'),

    # Authentication & User Routes
    path('login/', CustomLoginAPIView.as_view(), name='login'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('check-email/', views.check_email, name='check_email'),
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),

    # Product Routes
    path('products/', views.getProducts, name='products'),
    path('product/<int:pk>/', views.getProduct, name='product-detail'),

    # Cart Routes
    path('cart/', ViewCart.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('cart/update-item/<int:product_id>/', update_cart_item_quantity, name='update-cart-item'),
    path('cart/checkout/', views.checkout, name='checkout'),

    # Order Routes
    path('order/place/', PlaceOrderView.as_view(), name='order-place'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('order/<int:order_id>/status/', update_order_status, name='order-status-update'),

    # Service Routes
    path('services/', ServiceListView.as_view(), name='services'),
    path('service/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),

    # Booking Routes
    path('bookings/', BookingCreateView.as_view(), name='bookings'),
    path('bookings/status/', BookingStatusView.as_view(), name='booking-status'),
    path('booking/confirm/<int:pk>/', ConfirmBookingView.as_view(), name='booking-confirm'),


]