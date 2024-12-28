from rest_framework.decorators import api_view
from rest_framework.response import Response
from .products import products  # Importing product data from products.py

@api_view(['GET'])
def getRoutes(request):
    return Response({'message': 'Hello from Django!'})  # Simple response for API routes

@api_view(['GET'])
def getProducts(request):
    return Response({'products': products})  # Returning products from products.py
