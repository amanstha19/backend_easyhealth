from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .products import products  # Importing product data from products.py
from .serializers import ProductSerializer
from .models import Product
@api_view(['GET'])
def getRoutes(request):
    return Response({'message': 'Hello from Django!'})  # Simple response for API routes

@api_view(['GET'])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    print("Products Queryset:", products)
    return Response(serializer.data)
# Returning products from products.py

