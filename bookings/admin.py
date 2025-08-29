"""
Admin configuration for Bookings app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Booking, PassengerDetail, BookingHistory


class PassengerDetailInline(admin.TabularInline):
    """Inline admin for passenger details"""
    model = PassengerDetail
    extra = 0
    fields = ['title', 'first_name', 'last_name', 'date_of_birth', 'gender', 'id_type', 'id_number']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Enhanced Booking Admin"""
    
    list_display = [
        'booking_id', 'user', 'get_travel_info', 'number_of_seats',
        'total_price', 'status', 'payment_status', 'booking_date',
        'get_travel_date'
    ]
    list_filter = [
        'status', 'payment_status', 'booking_date',
        'travel_option__travel_type', 'travel_option__departure_datetime'
    ]
    search_fields = [
        'booking_id', 'user__username', 'user__email', 'user__first_name',
        'user__last_name', 'travel_option__travel_id', 'contact_email',
        'contact_phone'
    ]
    ordering = ['-booking_date']
    date_hierarchy = 'booking_date'
    
    inlines = [PassengerDetailInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': (
                'booking_id', 'user', 'travel_option',
                'number_of_seats', 'total_price'
            )
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Status', {
            'fields': (
                ('status', 'payment_status'),
                ('booking_date', 'confirmation_date', 'cancellation_date')
            )
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'passenger_details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('booking_reference', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'booking_reference', 'booking_date', 'confirmation_date',
        'cancellation_date', 'created_at', 'updated_at'
    ]
    
    def get_travel_info(self, obj):
        travel = obj.travel_option
        return f"{travel.travel_type} - {travel.source} → {travel.destination}"
    get_travel_info.short_description = 'Travel Details'
    get_travel_info.admin_order_field = 'travel_option__source'
    
    def get_travel_date(self, obj):
        date = obj.travel_option.departure_datetime
        if date < timezone.now():
            color = 'red'
        elif date < timezone.now() + timezone.timedelta(days=7):
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            date.strftime('%Y-%m-%d %H:%M')
        )
    get_travel_date.short_description = 'Travel Date'
    get_travel_date.admin_order_field = 'travel_option__departure_datetime'
    
    actions = ['confirm_bookings', 'cancel_bookings', 'mark_completed']
    
    def confirm_bookings(self, request, queryset):
        updated = 0
        for booking in queryset.filter(status='PENDING'):
            if booking.confirm_booking():
                updated += 1
        self.message_user(request, f'{updated} bookings confirmed.')
    confirm_bookings.short_description = 'Confirm selected bookings'
    
    def cancel_bookings(self, request, queryset):
        updated = 0
        for booking in queryset.filter(status='CONFIRMED'):
            if booking.cancel_booking():
                updated += 1
        self.message_user(request, f'{updated} bookings cancelled.')
    cancel_bookings.short_description = 'Cancel selected bookings'
    
    def mark_completed(self, request, queryset):
        updated = queryset.filter(
            status='CONFIRMED',
            travel_option__departure_datetime__lt=timezone.now()
        ).update(status='COMPLETED')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark past bookings as completed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'travel_option'
        ).prefetch_related('passengers')


@admin.register(PassengerDetail)
class PassengerDetailAdmin(admin.ModelAdmin):
    """Admin for Passenger Details"""
    
    list_display = [
        'full_name', 'get_booking_id', 'date_of_birth',
        'gender', 'id_type', 'id_number'
    ]
    list_filter = ['gender', 'id_type', 'booking__status']
    search_fields = [
        'first_name', 'last_name', 'id_number',
        'booking__booking_id', 'booking__user__username'
    ]
    
    def get_booking_id(self, obj):
        url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
        return format_html('<a href="{}">{}</a>', url, obj.booking.booking_id)
    get_booking_id.short_description = 'Booking ID'
    get_booking_id.admin_order_field = 'booking__booking_id'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking', 'booking__user')


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    """Admin for Booking History"""
    
    list_display = [
        'booking', 'status_from', 'status_to',
        'changed_by', 'timestamp'
    ]
    list_filter = ['status_from', 'status_to', 'timestamp']
    search_fields = [
        'booking__booking_id', 'changed_by__username', 'reason'
    ]
    ordering = ['-timestamp']
    
    readonly_fields = ['timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'booking', 'changed_by'
        )


# Custom admin view for booking analytics
class BookingAnalyticsAdmin(admin.ModelAdmin):
    """Custom admin view for booking analytics"""
    change_list_template = 'admin/booking_analytics.html'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = Booking.objects.all()
            
            # Status distribution
            status_stats = {}
            for choice in Booking.BOOKING_STATUS:
                status_stats[choice[1]] = qs.filter(status=choice[0]).count()
            
            # Revenue statistics
            total_revenue = qs.filter(
                status__in=['CONFIRMED', 'COMPLETED']
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
            
            # Recent bookings (last 30 days)
            recent_bookings = qs.filter(
                booking_date__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            
            # Travel type breakdown
            travel_type_stats = qs.values(
                'travel_option__travel_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            response.context_data.update({
                'status_stats': status_stats,
                'total_bookings': qs.count(),
                'total_revenue': total_revenue,
                'recent_bookings': recent_bookings,
                'travel_type_stats': travel_type_stats,
                'pending_bookings': qs.filter(status='PENDING').count(),
                'confirmed_bookings': qs.filter(status='CONFIRMED').count(),
            })
            
        except Exception as e:
            pass
        
        return response


# Add analytics to the admin
# admin.site.register(Booking, BookingAnalyticsAdmin)