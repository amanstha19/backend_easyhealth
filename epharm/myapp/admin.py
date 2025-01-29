from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Product, CustomUser, Cart, CartItem, Order, Service, Booking, BookingReport,Payment


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



class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'order', 'amount', 'status', 'stripe_payment_intent_id', 'created_at')
    list_filter = ('status',)
    search_fields = ('order__id', 'stripe_payment_intent_id')
    list_editable = ('status',)  # You can edit the status directly from the list view

    # Optionally add a link to the order from the payment view
    def view_order_link(self, obj):
        from django.urls import reverse
        return format_html('<a href="{}">View Order</a>', reverse('admin:myapp_order_change', args=[obj.order.id]))

    view_order_link.short_description = 'View Order'


admin.site.register(Payment, PaymentAdmin)