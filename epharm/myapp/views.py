from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer, UserSerializer, RegisterSerializer
from .models import Product
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


# Get all available routes
@api_view(['GET'])
def getRoutes(request):
    return Response({'message': 'Hello from Django!'})  # Simple response for API routes

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
        print(f"Error fetching product: {e}")
        return Response({'error': 'Product not found'}, status=404)

# Get user profile (protected route)
@api_view(['GET'])
def getUserProfile(request):
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

# Register API View to create a new user
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        # Get the data from the request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Create the user

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)

        # Return response with user data and tokens
        return Response({
            "user": {
                "username": user.username,
                "email": user.email,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)



# views.py

class CustomLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("Request Body:", request.data)  # Debugging: Print request data
        return super().post(request, *args, **kwargs)
