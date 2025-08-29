"""
Admin configuration for Travel app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import TravelOption, PopularRoute, TravelOperator


@admin.register(TravelOption)
class TravelOptionAdmin(admin.ModelAdmin):
    """Enhanced Travel Option Admin"""
    
    list_display = [
        'travel_id', 'travel_type', 'operator_name', 'get_route',
        'departure_datetime', 'base_price', 'available_seats',
        'total_seats', 'get_occupancy', 'status', 'is_featured'
    ]
    list_filter = [
        'travel_type', 'status', 'is_featured', 'departure_datetime',
        'operator_name', 'source', 'destination'
    ]
    search_fields = [
        'travel_id', 'operator_name', 'source', 'destination',
        'source_code', 'destination_code'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'departure_datetime'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('travel_id', 'travel_type', 'operator_name')
        }),
        ('Route Details', {
            'fields': (
                ('source', 'source_code'),
                ('destination', 'destination_code')
            )
        }),
        ('Schedule', {
            'fields': (
                ('departure_datetime', 'arrival_datetime'),
                'duration'
            )
        }),
        ('Pricing & Capacity', {
            'fields': (
                'base_price',
                ('available_seats', 'total_seats')
            )
        }),
        ('Additional Information', {
            'fields': (
                'description', 'amenities', 'baggage_allowance',
                'cancellation_policy'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['duration', 'created_at', 'updated_at']
    
    def get_route(self, obj):
        return f"{obj.source} → {obj.destination}"
    get_route.short_description = 'Route'
    get_route.admin_order_field = 'source'
    
    def get_occupancy(self, obj):
        percentage = obj.occupancy_percentage
        if percentage >= 80:
            color = 'red'
        elif percentage >= 60:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            percentage
        )
    get_occupancy.short_description = 'Occupancy'
    get_occupancy.admin_order_field = 'available_seats'
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'make_not_featured']
    
    def make_active(self, request, queryset):
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f'{updated} travel options marked as active.')
    make_active.short_description = 'Mark selected options as active'
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f'{updated} travel options marked as inactive.')
    make_inactive.short_description = 'Mark selected options as inactive'
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} travel options marked as featured.')
    make_featured.short_description = 'Mark selected options as featured'
    
    def make_not_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} travel options marked as not featured.')
    make_not_featured.short_description = 'Remove featured status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(PopularRoute)
class PopularRouteAdmin(admin.ModelAdmin):
    """Admin for Popular Routes"""
    
    list_display = [
        'source', 'destination', 'search_count',
        'booking_count', 'get_route_score', 'updated_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['source', 'destination']
    ordering = ['-booking_count', '-search_count']
    
    def get_route_score(self, obj):
        """Calculate route popularity score"""
        score = (obj.booking_count * 2) + obj.search_count
        return score
    get_route_score.short_description = 'Popularity Score'
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelOperator)
class TravelOperatorAdmin(admin.ModelAdmin):
    """Admin for Travel Operators"""
    
    list_display = [
        'name', 'operator_type', 'code', 'get_travel_count',
        'is_active', 'created_at'
    ]
    list_filter = ['operator_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'contact_email']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'operator_type', 'code', 'logo')
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'contact_phone', 'website')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_travel_count(self, obj):
        """Count travel options for this operator"""
        from .models import TravelOption
        count = TravelOption.objects.filter(operator_name=obj.name).count()
        if count > 0:
            url = reverse('admin:travel_traveloption_changelist') + f'?operator_name__exact={obj.name}'
            return format_html('<a href="{}">{} options</a>', url, count)
        return '0 options'
    get_travel_count.short_description = 'Travel Options'


# Note: TravelOption already registered above with TravelOptionAdmin