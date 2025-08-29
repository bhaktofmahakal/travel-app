"""
Booking Models for Travel Booking Application
Contains Booking model and related functionality
"""

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
import uuid


class BookingManager(models.Manager):
    """Custom manager for Booking model"""
    
    def active_bookings(self):
        """Return only confirmed bookings"""
        return self.filter(status='CONFIRMED')
    
    def cancelled_bookings(self):
        """Return only cancelled bookings"""
        return self.filter(status='CANCELLED')
    
    def user_bookings(self, user):
        """Return bookings for a specific user"""
        return self.filter(user=user).order_by('-booking_date')


class Booking(models.Model):
    """
    Model representing travel bookings
    """
    BOOKING_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # Core Fields
    booking_id = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    travel_option = models.ForeignKey(
        'travel.TravelOption',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    # Booking Details
    number_of_seats = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Passenger Information (JSON field for multiple passengers)
    passenger_details = models.JSONField(default=list)
    
    # Status and Dates
    status = models.CharField(max_length=10, choices=BOOKING_STATUS, default='PENDING')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(blank=True, null=True)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    
    # Additional Information
    special_requests = models.TextField(blank=True, null=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    
    # Metadata
    booking_reference = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = BookingManager()
    
    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['user', '-booking_date']),
            models.Index(fields=['status']),
            models.Index(fields=['travel_option']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('bookings:detail', kwargs={'booking_id': self.booking_id})
    
    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        if self.status in ['CANCELLED', 'COMPLETED']:
            return False
        
        # Don't allow cancellation if travel date has passed
        if self.is_past_travel:
            return False
        
        # Check if travel option allows cancellation
        if hasattr(self.travel_option, 'can_be_cancelled'):
            return self.travel_option.can_be_cancelled
        
        return True  # Default to allowing cancellation
    
    @property
    def is_past_travel(self):
        """Check if travel date has passed"""
        return self.travel_option.departure_datetime < timezone.now()
    
    @property
    def days_until_travel(self):
        """Get number of days until travel"""
        if self.is_past_travel:
            return 0
        
        delta = self.travel_option.departure_datetime.date() - timezone.now().date()
        return delta.days
    
    @property
    def refund_amount(self):
        """Calculate refund amount based on cancellation policy"""
        if not self.can_be_cancelled:
            return 0
        
        days_before = self.days_until_travel
        
        # Simple refund policy - can be enhanced
        if days_before >= 7:
            return float(self.total_price) * 0.9  # 90% refund
        elif days_before >= 3:
            return float(self.total_price) * 0.75  # 75% refund
        elif days_before >= 1:
            return float(self.total_price) * 0.5   # 50% refund
        else:
            return 0  # No refund
    
    def save(self, *args, **kwargs):
        """Override save to generate booking ID"""
        if not self.booking_id:
            self.booking_id = self.generate_booking_id()
        
        # Set confirmation date when status changes to confirmed
        if self.status == 'CONFIRMED' and not self.confirmation_date:
            self.confirmation_date = timezone.now()
        
        # Set cancellation date when status changes to cancelled
        if self.status == 'CANCELLED' and not self.cancellation_date:
            self.cancellation_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_booking_id(self):
        """Generate unique booking ID"""
        import random
        import string
        
        # Format: TKT + 7 digit random number (total 10 characters)
        random_part = ''.join(random.choices(string.digits, k=7))
        return f"TKT{random_part}"
    
    def confirm_booking(self):
        """Confirm the booking"""
        if self.status == 'PENDING':
            self.status = 'CONFIRMED'
            self.confirmation_date = timezone.now()
            self.payment_status = 'COMPLETED'
            self.save()
            return True
        return False
    
    def cancel_booking(self):
        """Cancel the booking and restore seats"""
        if self.can_be_cancelled and self.status == 'CONFIRMED':
            self.status = 'CANCELLED'
            self.cancellation_date = timezone.now()
            
            # Restore available seats to travel option
            self.travel_option.increase_available_seats(self.number_of_seats)
            
            self.save()
            return True
        return False


class PassengerDetail(models.Model):
    """
    Model for individual passenger details in a booking
    """
    TITLE_CHOICES = [
        ('MR', 'Mr.'),
        ('MRS', 'Mrs.'),
        ('MS', 'Ms.'),
        ('DR', 'Dr.'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE,
        related_name='passengers'
    )
    
    # Personal Information
    title = models.CharField(max_length=3, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Travel Documents
    id_type = models.CharField(max_length=20, default='Passport')  # Passport, Aadhar, etc.
    id_number = models.CharField(max_length=50)
    
    # Additional Information
    seat_preference = models.CharField(max_length=20, blank=True, null=True)
    meal_preference = models.CharField(max_length=20, blank=True, null=True)
    special_assistance = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'passenger_details'
        verbose_name = 'Passenger Detail'
        verbose_name_plural = 'Passenger Details'
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class BookingHistory(models.Model):
    """
    Model to track booking status changes and history
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='history'
    )
    status_from = models.CharField(max_length=10, choices=Booking.BOOKING_STATUS)
    status_to = models.CharField(max_length=10, choices=Booking.BOOKING_STATUS)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_history'
        verbose_name = 'Booking History'
        verbose_name_plural = 'Booking Histories'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.booking.booking_id}: {self.status_from} → {self.status_to}"