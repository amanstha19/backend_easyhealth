# Generated by Django 5.1.5 on 2025-01-29 07:58

import django.core.validators
import django.db.models.deletion
import myapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0015_rename_address_order_full_address_order_first_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='full_address',
            new_name='address',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='report_file',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='report_uploaded_at',
        ),
        migrations.RemoveField(
            model_name='order',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='phone_number',
        ),
        migrations.CreateModel(
            name='BookingReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_file', models.FileField(upload_to='reports/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), myapp.models.validate_file_size])),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='myapp.booking')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
