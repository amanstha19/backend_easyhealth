from django.db import models

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
            return self.username









