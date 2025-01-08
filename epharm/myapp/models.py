from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class Product(models.Model):
    objects = None
    id = models.AutoField(primary_key=True)
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

    generic_name = models.CharField(max_length=200, null=True, blank=True)  # Scientific or generic name
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
        # Return the generic name if available, otherwise return the name or a fallback string
        return self.generic_name if self.generic_name else self.name if self.name else "Unnamed Product"\




class CustomUser(AbstractUser):
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.username
