from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import Product, CustomUser, Cart, CartItem, Order, Service, Booking, BookingReport


# Admin for Product model
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'price', 'category', 'stock', 'prescription_required', 'created_at')
    search_fields = ('name', 'generic_name', 'description')
    list_filter = ('category', 'prescription_required')

admin.site.register(Product, ProductAdmin)

# Admin for CustomUser model
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'city', 'country', 'phone')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'city', 'country', 'phone')

    # Add custom fields to the user creation/edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'city', 'country')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone', 'city', 'country')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# Admin for Cart model
class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

admin.site.register(Cart, CartAdmin)

# Admin for CartItem model
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'cart_user')
    search_fields = ('product__name',)
    list_filter = ('product__category',)

    def cart_user(self, obj):
        return obj.cart.user.username
    cart_user.short_description = 'Cart User'

admin.site.register(CartItem, CartItemAdmin)

# Admin for Order model
from django.contrib import admin
from .models import Order, CartItem


class OrderAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'user', 'user_full_name','address', 'total_price', 'status', 'created_at', 'prescription', 'cart_items')
    list_editable = ('status',)  # Make status editable directly in the admin panel
    list_filter = ('status',)
    search_fields = ('user__username', 'status', 'user__first_name', 'user__last_name', 'user__phone')

    # Adding custom methods for user full name and cart items
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    user_full_name.admin_order_field = 'user__first_name'  # Allow ordering by first name
    user_full_name.short_description = 'Full Name'

    def user_phone(self, obj):
        return obj.user.phone

    user_phone.short_description = 'Phone'

    def cart_items(self, obj):
        cart_items = CartItem.objects.filter(order=obj)
        return ", ".join([f"{item.quantity} x {item.product.name}" for item in cart_items])

    cart_items.short_description = 'Cart Items'


admin.site.register(Order, OrderAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')  # Customize what to display in the list view
    search_fields = ('name',)  # Make name searchable in the admin panel
    list_filter = ('price',)  # Add filter by price if needed

# Register the Booking model
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'email', 'service', 'booking_date', 'appointment_time', 'status', 'created_at')
    search_fields = ('name', 'email', 'mobile_number', 'service__name')  # Search by name, email, mobile, or service name
    list_filter = ('status', 'booking_date', 'service')  # Add filters for status, date, and service
    date_hierarchy = 'booking_date'  # Add a date hierarchy filter for easy navigation by date

# Register the BookingReport model
@admin.register(BookingReport)
class BookingReportAdmin(admin.ModelAdmin):
    list_display = ('booking', 'report_file', 'uploaded_at', 'notes')
    search_fields = ('booking__name', 'booking__service__name')  # Search by booking name and service
    list_filter = ('uploaded_at',)  # Add filter by upload date

from django.contrib import admin
from .models import userPayment

@admin.register(userPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_uuid',
        'get_user_info',  # Displays user info
        'get_order_details',  # Displays order details
        'transaction_code',
        'amount',
        'tax_amount',
        'total_amount',
        'status',
        'created_at'
    )
    search_fields = (
        'transaction_uuid',
        'transaction_code',
        'user__username',  # Searching by username of the linked user
        'user__email'  # Searching by email of the linked user
    )
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    def get_user_info(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"  # Show the username and email if the user exists
        return "No user assigned"  # If no user is linked to the payment
    get_user_info.short_description = 'User'

    def get_order_details(self, obj):
        return obj.get_order_details()
    get_order_details.short_description = 'Order Details'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)  # Only show 'user' field in the admin form
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_uuid',
                'transaction_code',
                'amount',
                'tax_amount',
                'total_amount',
                'product_code',
                'status'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Collapse this section by default
        }),
        ('Order Details', {
            'fields': ('order',),  # Display order info
            'classes': ('collapse',)
        }),
    )
