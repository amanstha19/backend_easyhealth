from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'price', 'created_at')
    search_fields = ['name', 'generic_name']  # Optional: allows searching by these fields
    list_filter = ['category']  # Optional: adds a filter sidebar by category

admin.site.register(Product, ProductAdmin)




from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('city', 'country', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('city', 'country', 'phone')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
