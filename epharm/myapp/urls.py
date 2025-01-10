from django.urls import path
from . import views
from .views import CustomLoginAPIView, UserProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    # API Routes
    path('', views.getRoutes, name='getRoutes'),  # Accessible at /api/

    # Product Routes
    path('products/', views.getProducts, name='getProducts'),  # Accessible at /api/products
    path('product/<int:pk>/', views.getProduct, name='getProduct'),  # Accessible at /api/product/<product_id>

    # Authentication & Authorization Routes
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login route to get tokens
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token route
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),  # Verify token route

    # User Profile Route (protected)
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),  # Profile endpoint

    # Registration Route (Signup)
    path('register/', views.RegisterAPIView.as_view(), name='register'),  # Register a new user
    path('login/', CustomLoginAPIView.as_view(), name='login'),  # Custom login view for JWT tokens

    # Check if an email is already registered
    path('check-email/', views.check_email, name='check_email'),  # Check if an email is already registered

    # Cart Routes
    path('cart/', views.ViewCart.as_view(), name='view_cart'),  # View the cart and calculate total
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add product to cart
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),  # Remove product from cart
    path('cart/checkout/', views.checkout, name='checkout'),  # Proceed with checkout and clear cart
]
