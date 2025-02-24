from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from .models import (
    Product, CustomUser, Cart, CartItem, Order, Service, Booking, BookingReport, userPayment
)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'price', 'category', 'stock', 'stock_status', 'prescription_required', 'created_at')
    list_editable = ('stock',)
    search_fields = ('name', 'generic_name', 'description')
    list_filter = ('category', 'prescription_required')
    readonly_fields = ('created_at', 'updated_at')

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        elif obj.stock < 10:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: green;">In Stock ({})</span>', obj.stock)
    stock_status.short_description = 'Stock Status'

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Product.objects.get(pk=obj.pk)
            if old_obj.stock != obj.stock:
                stock_change = obj.stock - old_obj.stock
                operation = 'increased' if stock_change > 0 else 'decreased'
                messages.add_message(request, messages.INFO, f'Stock {operation} by {abs(stock_change)} units for {obj.name}')
        super().save_model(request, obj, form, change)

admin.site.register(Product, ProductAdmin)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'city', 'country', 'phone')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'city', 'country', 'phone')
    fieldsets = UserAdmin.fieldsets + (('Additional Info', {'fields': ('phone', 'city', 'country')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Additional Info', {'fields': ('phone', 'city', 'country')}),)

admin.site.register(CustomUser, CustomUserAdmin)

class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

admin.site.register(Cart, CartAdmin)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'cart_user')
    search_fields = ('product__name',)
    list_filter = ('product__category',)

    def cart_user(self, obj):
        return obj.cart.user.username
    cart_user.short_description = 'Cart User'

admin.site.register(CartItem, CartItemAdmin)

class CartItemInline(admin.TabularInline):
    model = CartItem
    readonly_fields = ('product', 'quantity', 'prescription_file')
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at', 'updated_at', 'view_items')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    def view_items(self, obj):
        items = CartItem.objects.filter(order=obj)
        return format_html("<br>".join([f"{item.quantity}x {item.product.name}" for item in items]))
    view_items.short_description = "Order Items"

admin.site.register(Service, admin.ModelAdmin)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'email', 'service', 'booking_date', 'appointment_time', 'status', 'created_at')
    search_fields = ('name', 'email', 'mobile_number', 'service__name')
    list_filter = ('status', 'booking_date', 'service')
    date_hierarchy = 'booking_date'

@admin.register(BookingReport)
class BookingReportAdmin(admin.ModelAdmin):
    list_display = ('booking', 'report_file', 'uploaded_at', 'notes')
    search_fields = ('booking__name', 'booking__service__name')
    list_filter = ('uploaded_at',)

@admin.register(userPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_uuid', 'get_user_info', 'get_order_details', 'transaction_code', 'amount', 'tax_amount', 'total_amount', 'status', 'created_at')
    search_fields = ('transaction_uuid', 'transaction_code', 'user__username', 'user__email')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    def get_user_info(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        return "No user assigned"
    get_user_info.short_description = 'User'

    def get_order_details(self, obj):
        return obj.get_order_details()
    get_order_details.short_description = 'Order Details'
