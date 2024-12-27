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

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # Slug field
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    prescription_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
