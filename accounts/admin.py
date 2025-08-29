"""
Admin configuration for Accounts app
Professional Django Admin with enhanced functionality
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserPreferences


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Enhanced User Admin with additional fields"""
    
    list_display = [
        'username', 'email', 'get_full_name', 'is_verified',
        'is_active', 'is_staff', 'date_joined', 'last_login'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'is_verified',
        'date_joined', 'last_login'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': (
                'phone_number', 'date_of_birth', 'profile_picture',
                'address', 'city', 'state', 'country', 'postal_code'
            )
        }),
        ('Account Status', {
            'fields': ('is_verified', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('preferences')
    
    actions = ['make_verified', 'make_unverified']
    
    def make_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users marked as verified.')
    make_verified.short_description = 'Mark selected users as verified'
    
    def make_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users marked as unverified.')
    make_unverified.short_description = 'Mark selected users as unverified'


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Admin for User Preferences"""
    
    list_display = [
        'user', 'preferred_currency', 'preferred_language',
        'newsletter_subscription', 'sms_notifications', 'email_notifications'
    ]
    list_filter = [
        'preferred_currency', 'preferred_language', 'newsletter_subscription',
        'sms_notifications', 'email_notifications'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('preferred_currency', 'preferred_language')
        }),
        ('Notifications', {
            'fields': ('newsletter_subscription', 'sms_notifications', 'email_notifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


# Customize admin site
admin.site.site_header = "Travel Booking Administration"
admin.site.site_title = "Travel Booking Admin"
admin.site.index_title = "Welcome to Travel Booking Administration"