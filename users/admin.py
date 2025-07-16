from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('OOX Role', {'fields': ('role', 'phone')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('OOX Role', {'fields': ('role', 'phone')}),
    ) 