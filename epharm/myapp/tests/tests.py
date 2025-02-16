from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from myapp.models import CustomUser, Product, Order, CartItem
from rest_framework import status
from django.core.exceptions import ValidationError


class OrderTests(TestCase):
    """Tests related to the Order model."""

    def setUp(self):
        """Set up the test environment."""
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(name='Painkiller', price=10.99, stock=100, category='OTC')

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        self.product.delete()


class CartItemTests(TestCase):
    """Tests related to the CartItem model."""

    def setUp(self):
        """Set up the test environment for CartItem."""
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(name='Painkiller', price=10.99, stock=100, category='OTC')
        self.order = Order.objects.create(user=self.user, total_price=10.99, status='pending', address='123 Test St')

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        self.product.delete()
        self.order.delete()

    def test_add_product_to_order(self):
        """Test adding a product to an order."""
        cart_item = CartItem.objects.create(order=self.order, product=self.product, quantity=2)

        self.assertEqual(cart_item.product.name, 'Painkiller')
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(self.order.cartitem_set.count(), 1)


class OrderAPITests(TestCase):
    """API Tests related to the Order model."""

    def setUp(self):
        """Set up the test environment for API testing."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(name='Painkiller', price=10.99, stock=100, category='OTC')

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        self.product.delete()

    def test_create_order_api(self):
        """Test creating an order via API."""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-place')  # Adjusted to match the correct URL for placing an order
        data = {
            'user': self.user.id,
            'total_price': 10.99,
            'status': 'pending',
            'address': '123 Test St',
            'prescription': SimpleUploadedFile('test_prescription.pdf', b'file_content', content_type='application/pdf')
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['prescription'].endswith('test_prescription.pdf'))


class EdgeCaseTests(TestCase):
    """Tests for edge cases in the system."""

    def setUp(self):
        """Set up the test environment for edge cases."""
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(name='Painkiller', price=10.99, stock=100, category='OTC')

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        self.product.delete()

    def test_missing_address_in_order(self):
        """Test that creating an order without an address raises a validation error."""
        order = Order(user=self.user, total_price=10.99, status='pending', address='')

        with self.assertRaises(ValidationError):
            order.full_clean()  # This will validate the model fields, including address


class DeletionTests(TestCase):
    """Tests related to object deletions and integrity."""

    def setUp(self):
        """Set up the test environment for deletion tests."""
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(name='Painkiller', price=10.99, stock=100, category='OTC')
        self.order = Order.objects.create(user=self.user, total_price=10.99, status='pending', address='123 Test St')
        self.cart_item = CartItem.objects.create(order=self.order, product=self.product, quantity=2)

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        self.product.delete()
        # Make sure to delete order and cart item separately to avoid issues with cascade deletions
        self.cart_item.delete()
        self.order.delete()

    def test_delete_order_with_related_items(self):
        """Test that deleting an order correctly removes related cart items."""
        self.order.delete()
        self.assertEqual(CartItem.objects.count(), 0)  # The related cart item should be deleted
