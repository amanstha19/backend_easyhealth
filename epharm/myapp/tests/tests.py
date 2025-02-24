import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from myapp.models import Product, Service, Order, userPayment
import json
import uuid

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
        first_name='Test',
        last_name='User',
        city='Test City',
        country='Test Country',
        phone='1234567890'
    )
    return user

@pytest.fixture
def authenticated_client(api_client, create_user):
    url = reverse('myapp:login')
    resp = api_client.post(url, {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }, format='json')
    token = resp.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client

@pytest.fixture
def sample_product():
    return Product.objects.create(
        name='Test Product',
        generic_name='Generic Test',
        description='A test product',
        price=10.99,
        stock=100,
        category='Test Category',
        prescription_required=False
    )

@pytest.fixture
def sample_service():
    return Service.objects.create(
        name='Test Service',
        description='A test service',
        price=50.00,
        duration=60
    )

# Authentication Tests
@pytest.mark.django_db
def test_register_new_user(api_client):
    url = reverse('myapp:register')
    payload = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword123',
        'first_name': 'New',
        'last_name': 'User',
        'city': 'New City',
        'country': 'New Country',
        'phone': '9876543210'
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username='newuser').exists()
    assert 'refresh' in response.data
    assert 'access' in response.data

@pytest.mark.django_db
def test_login_user(api_client, create_user):
    url = reverse('myapp:login')
    payload = {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'refresh' in response.data
    assert 'access' in response.data

# Product Tests
@pytest.mark.django_db
def test_get_products(api_client, sample_product):
    url = reverse('myapp:products')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Test Product'

@pytest.mark.django_db
def test_get_product_detail(api_client, sample_product):
    url = reverse('myapp:product-detail', kwargs={'pk': sample_product.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Test Product'
    assert response.data['price'] == '10.99'

# Cart Tests
@pytest.mark.django_db
def test_add_to_cart(authenticated_client, sample_product):
    url = reverse('myapp:add-to-cart', kwargs={'product_id': sample_product.id})
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert 'cart_items' in response.data
    assert len(response.data['cart_items']) == 1
    assert response.data['cart_items'][0]['product_id'] == sample_product.id
    assert response.data['cart_items'][0]['quantity'] == 1
    assert response.data['total_price'] == float(sample_product.price)

# Order Tests
@pytest.mark.django_db
def test_place_order(authenticated_client, sample_product):
    # First add item to cart
    add_url = reverse('myapp:add-to-cart', kwargs={'product_id': sample_product.id})
    authenticated_client.post(add_url)

    # Get cart items
    cart_url = reverse('myapp:cart')
    cart_response = authenticated_client.get(cart_url)
    cart_items = cart_response.data['cart_items']

    # Place order
    url = reverse('myapp:order-place')
    payload = {
        'cart_items': json.dumps(cart_items),
        'address': '123 Test Street, Test City'
    }
    response = authenticated_client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert 'order_id' in response.data

    # Verify order was created
    order = Order.objects.get(id=response.data['order_id'])
    assert order.total_price == sample_product.price
    assert order.address == '123 Test Street, Test City'

# Payment Tests
@pytest.mark.django_db
def test_process_payment(authenticated_client, create_user):
    transaction_uuid = str(uuid.uuid4())
    url = reverse('myapp:process-payment')
    payload = {
        'amount': 100.00,
        'tax_amount': 10.00,
        'transaction_uuid': transaction_uuid
    }
    response = authenticated_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert 'total_amount' in response.data
    assert float(response.data['total_amount']) == 110.00
    assert response.data['transaction_uuid'] == transaction_uuid

    # Verify payment record was created
    payment = userPayment.objects.get(transaction_uuid=transaction_uuid)
    assert payment.amount == 100.00
    assert payment.tax_amount == 10.00
    assert payment.status == 'PENDING'

@pytest.mark.django_db
def test_payment_callback(authenticated_client, create_user):
    # First create a payment
    transaction_uuid = str(uuid.uuid4())
    userPayment.objects.create(
        amount=100.00,
        tax_amount=10.00,
        total_amount=110.00,
        transaction_uuid=transaction_uuid,
        status='PENDING',
        user=create_user
    )

    # Then simulate callback
    url = reverse('myapp:process-payment')
    payload = {
        'transaction_uuid': transaction_uuid,
        'status': 'SUCCESS',
        'transaction_code': 'TEST123',
        'data': 'test-data'
    }
    response = authenticated_client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Payment successful'

    # Verify payment was updated
    payment = userPayment.objects.get(transaction_uuid=transaction_uuid)
    assert payment.status == 'SUCCESS'
    assert payment.transaction_code == 'TEST123'
