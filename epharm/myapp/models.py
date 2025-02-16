from datetime import timezone
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.exceptions import ValidationError
from django.conf import settings

# Custom User model
class CustomUser(AbstractUser):
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.username

# Product model
class Product(models.Model):
    CATEGORIES = (
        ('OTC', 'Over-the-Counter'),
        ('RX', 'Prescription Medicines'),
        ('SUP', 'Supplements & Vitamins'),
        ('WOM', 'Women’s Health'),
        ('MEN', 'Men’s Health'),
        ('PED', 'Pediatric Medicines'),
        ('HERB', 'Herbal & Ayurvedic'),
        ('DIAG', 'Diagnostics & Medical Devices'),
        ('FIRST', 'First Aid'),
    )

    id = models.AutoField(primary_key=True)
    generic_name = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    prescription_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.generic_name if self.generic_name else self.name if self.name else "Unnamed Product"



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    address = models.TextField(null=False, default="Unknown Address")  # Add a default value
    prescription = models.FileField(upload_to='prescriptions/', null=True, blank=True)  # Ensure this exists
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        cart_items = self.cartitem_set.all()  # Get related cart items
        cart_items_str = ", ".join([f"{item.quantity} x {item.product.name}" for item in cart_items])
        return (f"Order {self.id} - {self.user.first_name} {self.user.last_name} ({self.user.phone}) "
                f"Status: {self.status} - Address: {self.address} - Cart Items: {cart_items_str}")

# CartItem model\

class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_items', on_delete=models.CASCADE,default=1)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)  # Link to the order
    prescription_file = models.FileField(upload_to='cart_prescriptions/', null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

from django.core.validators import FileExtensionValidator

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    booking_date = models.DateField()
    appointment_time = models.TimeField()
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.service.name} - {self.booking_date}"

    class Meta:
        ordering = ['-created_at']
        # Prevent double booking
        constraints = [
            models.UniqueConstraint(
                fields=['service', 'booking_date', 'appointment_time'],
                name='unique_booking_slot'
            )
        ]


def validate_file_size(value):
    limit = 20 * 1024 * 1024  # 5MB
    if value.size > limit:
        raise ValidationError("File size should not exceed 5MB.")


class BookingReport(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reports')
    report_file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), validate_file_size])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Report for {self.booking.name} - {self.booking.service.name}"

    class Meta:
        ordering = ['-uploaded_at']

from django.db import models
from django.utils import timezone
class userPayment(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_payments', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    products = models.ManyToManyField(Product, blank=True)  # If direct product linkage is needed
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_uuid = models.CharField(max_length=100, unique=True)
    transaction_code = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    product_code = models.CharField(max_length=50, default='EPAYTEST')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_uuid} - {self.status}"

    def get_order_details(self):
        if self.order:
            return f"Order ID: {self.order.id}, Status: {self.order.status}, Address: {self.order.address}, Total: {self.order.total_price}"
        return "No order details available"