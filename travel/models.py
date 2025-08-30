"""
Travel Models for Travel Booking Application
Contains TravelOption model with all travel types (Flight, Train, Bus)
"""

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


class TravelOption(models.Model):
    """
    Model representing travel options (Flight, Train, Bus)
    """
    TRAVEL_TYPES = [
        ('FLIGHT', 'Flight'),
        ('TRAIN', 'Train'),
        ('BUS', 'Bus'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Core Fields
    travel_id = models.CharField(max_length=20, unique=True, db_index=True)
    travel_type = models.CharField(max_length=10, choices=TRAVEL_TYPES)
    operator_name = models.CharField(max_length=100)  # Airline/Railway/Bus operator
    
    # Route Information
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    source_code = models.CharField(max_length=10, blank=True, null=True)  # Airport/Station codes
    destination_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Timing
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    duration = models.DurationField()  # Calculated automatically
    
    # Pricing and Capacity
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    available_seats = models.PositiveIntegerField()
    total_seats = models.PositiveIntegerField()
    
    # Additional Information
    description = models.TextField(blank=True, null=True)
    amenities = models.JSONField(default=list, blank=True)  # List of amenities
    baggage_allowance = models.CharField(max_length=100, blank=True, null=True)
    cancellation_policy = models.TextField(blank=True, null=True)
    
    # Status and Metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'travel_options'
        verbose_name = 'Travel Option'
        verbose_name_plural = 'Travel Options'
        ordering = ['departure_datetime']
        indexes = [
            models.Index(fields=['travel_type', 'source', 'destination']),
            models.Index(fields=['departure_datetime']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.travel_id} - {self.source} to {self.destination} ({self.travel_type})"
    
    def get_absolute_url(self):
        return reverse('travel:detail', kwargs={'pk': self.pk})
    
    @property
    def is_available(self):
        """Check if travel option is available for booking"""
        return (
            self.status == 'ACTIVE' and 
            self.available_seats > 0 and 
            self.departure_datetime > timezone.now()
        )
    
    @property
    def is_almost_full(self):
        """Check if less than 20% seats are available"""
        if self.total_seats == 0:
            return False
        return (self.available_seats / self.total_seats) < 0.2
    
    @property
    def occupancy_percentage(self):
        """Calculate occupancy percentage"""
        if self.total_seats == 0:
            return 0
        return round(((self.total_seats - self.available_seats) / self.total_seats) * 100, 1)
    
    @property
    def time_until_departure(self):
        """Get time until departure"""
        if self.departure_datetime <= timezone.now():
            return timedelta(0)
        return self.departure_datetime - timezone.now()
    
    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled (24 hours before departure)"""
        cancellation_deadline = self.departure_datetime - timedelta(hours=24)
        return timezone.now() < cancellation_deadline
    
    def save(self, *args, **kwargs):
        """Override save to calculate duration"""
        if self.departure_datetime and self.arrival_datetime:
            self.duration = self.arrival_datetime - self.departure_datetime
        
        # Generate travel_id if not provided
        if not self.travel_id:
            self.travel_id = self.generate_travel_id()
        
        super().save(*args, **kwargs)
    
    def generate_travel_id(self):
        """Generate unique travel ID"""
        import random
        import string
        
        prefix_map = {
            'FLIGHT': 'FL',
            'TRAIN': 'TR',
            'BUS': 'BU'
        }
        
        prefix = prefix_map.get(self.travel_type, 'XX')
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{random_part}"
    
    def reduce_available_seats(self, count=1):
        """Reduce available seats after booking"""
        if self.available_seats >= count:
            self.available_seats -= count
            self.save(update_fields=['available_seats'])
            return True
        return False
    
    def increase_available_seats(self, count=1):
        """Increase available seats after cancellation"""
        if self.available_seats + count <= self.total_seats:
            self.available_seats += count
            self.save(update_fields=['available_seats'])
            return True
        return False


class PopularRoute(models.Model):
    """
    Model to track popular routes for recommendations
    """
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    search_count = models.PositiveIntegerField(default=0)
    booking_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'popular_routes'
        verbose_name = 'Popular Route'
        verbose_name_plural = 'Popular Routes'
        unique_together = ['source', 'destination']
    
    def __str__(self):
        return f"{self.source} → {self.destination}"
    
    def increment_search_count(self):
        """Increment search count for this route"""
        self.search_count += 1
        self.save(update_fields=['search_count'])
    
    def increment_booking_count(self):
        """Increment booking count for this route"""
        self.booking_count += 1
        self.save(update_fields=['booking_count'])
    
    @classmethod
    def get_or_create_route(cls, source, destination):
        """Get or create a popular route"""
        route, created = cls.objects.get_or_create(
            source=source,
            destination=destination
        )
        return route


class TravelOperator(models.Model):
    """
    Model for travel operators (Airlines, Railways, Bus companies)
    """
    OPERATOR_TYPES = [
        ('AIRLINE', 'Airline'),
        ('RAILWAY', 'Railway'),
        ('BUS_COMPANY', 'Bus Company'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    operator_type = models.CharField(max_length=12, choices=OPERATOR_TYPES)
    code = models.CharField(max_length=10, unique=True)  # IATA code for airlines
    # Temporarily using CharField for Render deployment (no Pillow needed)
    logo = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'travel_operators'
        verbose_name = 'Travel Operator'
        verbose_name_plural = 'Travel Operators'
    
    def __str__(self):
        return f"{self.name} ({self.operator_type})"