# Generated by Django 5.1.5 on 2025-01-30 14:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0026_remove_esewapayment_delivery_charge_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='order',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='user',
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('esewa_id', models.CharField(max_length=50)),
                ('payment_status', models.CharField(default='PENDING', max_length=50)),
                ('payment_response', models.JSONField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.order')),
            ],
        ),
        migrations.DeleteModel(
            name='EsewaPayment',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
