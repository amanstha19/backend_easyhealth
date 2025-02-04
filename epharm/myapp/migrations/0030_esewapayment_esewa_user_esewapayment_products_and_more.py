# Generated by Django 5.1.5 on 2025-02-03 15:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0029_remove_esewapayment_delivery_charge_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='esewapayment',
            name='esewa_user',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='esewapayment',
            name='products',
            field=models.ManyToManyField(blank=True, to='myapp.product'),
        ),
        migrations.AddField(
            model_name='esewapayment',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='esewa_payments', to=settings.AUTH_USER_MODEL),
        ),
    ]
