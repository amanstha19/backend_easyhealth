from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .products import products  # Importing product data from products.py
from .serializers import ProductSerializer
from .models import Product
from django.shortcuts import get_object_or_404
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


@api_view(['GET'])
def getProduct(request, pk):
    # Fetch the product by its id
    product = get_object_or_404(Product, id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)