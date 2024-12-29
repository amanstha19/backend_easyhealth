# Generated by Django 5.1.4 on 2024-12-29 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=200, unique=True)),
                ('category', models.CharField(choices=[('OTC', 'Over-the-Counter'), ('RX', 'Prescription Medicines'), ('SUP', 'Supplements & Vitamins'), ('WOM', 'Women’s Health'), ('MEN', 'Men’s Health'), ('PED', 'Pediatric Medicines'), ('HERB', 'Herbal & Ayurvedic'), ('DIAG', 'Diagnostics & Medical Devices'), ('FIRST', 'First Aid')], max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stock', models.PositiveIntegerField()),
                ('prescription_required', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
