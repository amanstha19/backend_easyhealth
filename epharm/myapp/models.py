from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    objects = None
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
        return self.generic_name if self.generic_name else self.name if self.name else "Unnamed Product"
