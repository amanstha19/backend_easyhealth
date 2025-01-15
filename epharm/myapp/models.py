from django.db import models
from django.contrib.auth.models import AbstractUser

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

# Order model
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')  # Example: Pending, Completed, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address = models.TextField(null=True, blank=True)  # Optional: Store address with the order

    def __str__(self):
        return f"Order {self.id} - {self.status}"

# CartItem model
class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)  # Link to the order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# Cart model
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')
    items = models.ManyToManyField(CartItem, blank=True)

    def __str__(self):
        return f"Cart of {self.user.username}"  # Referring to user’s username directly
