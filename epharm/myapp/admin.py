from django.contrib import admin
from .models import Product, CustomUser, Cart, CartItem, Order

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

    # Custom method to show the related cart's user
    def cart_user(self, obj):
        return obj.cart.user.username
    cart_user.short_description = 'Cart User'

admin.site.register(CartItem, CartItemAdmin)

# Admin for Order model
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at', 'prescription')
    list_editable = ('status',)  # Make status editable directly in the admin panel
    list_filter = ('status',)
    search_fields = ('user__username', 'status')

admin.site.register(Order, OrderAdmin)
