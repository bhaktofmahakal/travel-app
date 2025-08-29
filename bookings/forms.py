"""
Forms for Booking Management
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Div, Fieldset
from crispy_forms.bootstrap import FormActions
from .models import Booking, PassengerDetail

User = get_user_model()


class BookingForm(forms.ModelForm):
    """
    Form for creating a new booking
    """
    number_of_seats = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        })
    )
    contact_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    contact_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 1234567890'
        })
    )
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requests or requirements...'
        })
    )
    
    # Terms and conditions
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Booking
        fields = ['number_of_seats', 'contact_email', 'contact_phone', 'special_requests']
    
    def __init__(self, travel_option=None, user=None, *args, **kwargs):
        self.travel_option = travel_option
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Pre-fill user information if available
        if user and user.is_authenticated:
            self.fields['contact_email'].initial = user.email
            self.fields['contact_phone'].initial = user.phone_number
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'booking-form'
        
        self.helper.layout = Layout(
            HTML('<h4>Booking Details</h4><hr>'),
            Row(
                Column('number_of_seats', css_class='col-md-6'),
                Column(
                    HTML(f'<div class="form-group"><label>Available Seats:</label><p class="form-control-plaintext text-success"><strong>{travel_option.available_seats if travel_option else "N/A"}</strong></p></div>'),
                    css_class='col-md-6'
                ),
            ),
            HTML('<h4>Contact Information</h4><hr>'),
            Row(
                Column('contact_email', css_class='col-md-6'),
                Column('contact_phone', css_class='col-md-6'),
            ),
            'special_requests',
            HTML('<h4>Terms & Conditions</h4><hr>'),
            Div(
                'agree_terms',
                HTML('<label for="id_agree_terms" class="form-check-label">I agree to the <a href="#" data-bs-toggle="modal" data-bs-target="#termsModal">Terms and Conditions</a></label>'),
                css_class='form-check'
            ),
            HTML('<hr>'),
            FormActions(
                Submit('book', 'Proceed to Payment', css_class='btn btn-primary btn-lg'),
                HTML('<a href="javascript:history.back()" class="btn btn-secondary">Back</a>')
            )
        )
    
    def clean_number_of_seats(self):
        seats = self.cleaned_data['number_of_seats']
        
        if self.travel_option:
            if seats > self.travel_option.available_seats:
                raise forms.ValidationError(f"Only {self.travel_option.available_seats} seats are available.")
        
        return seats
    
    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.user = self.user
        booking.travel_option = self.travel_option
        booking.total_price = booking.number_of_seats * self.travel_option.base_price
        
        if commit:
            booking.save()
            # Reduce available seats
            self.travel_option.reduce_available_seats(booking.number_of_seats)
        
        return booking


class PassengerDetailForm(forms.ModelForm):
    """
    Form for passenger details
    """
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = PassengerDetail
        fields = [
            'title', 'first_name', 'last_name', 'date_of_birth',
            'gender', 'id_type', 'id_number', 'seat_preference',
            'meal_preference', 'special_assistance'
        ]
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'id_type': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'seat_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Window, Aisle'
            }),
            'meal_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Vegetarian, Non-Veg'
            }),
            'special_assistance': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special assistance required...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render form tags (handled by parent formset)


class PassengerFormSet(forms.BaseModelFormSet):
    """
    Formset for handling multiple passenger details
    """
    def clean(self):
        """Validate the formset"""
        if any(self.errors):
            return
        
        # Check for duplicate passengers (same name and DOB)
        passengers = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                date_of_birth = form.cleaned_data.get('date_of_birth')
                
                passenger_key = (first_name, last_name, date_of_birth)
                if passenger_key in passengers:
                    raise forms.ValidationError("Duplicate passenger information found.")
                passengers.append(passenger_key)


# Create the formset
PassengerDetailFormSet = forms.modelformset_factory(
    PassengerDetail,
    form=PassengerDetailForm,
    formset=PassengerFormSet,
    extra=1,
    can_delete=False
)


class BookingSearchForm(forms.Form):
    """
    Form for searching bookings
    """
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    booking_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Booking ID',
            'class': 'form-control'
        })
    )
    travel_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('FLIGHT', 'Flight'),
            ('TRAIN', 'Train'),
            ('BUS', 'Bus'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'booking-search-form'
        
        self.helper.layout = Layout(
            Row(
                Column('booking_id', css_class='col-md-3'),
                Column('travel_type', css_class='col-md-2'),
                Column('status', css_class='col-md-2'),
                Column('date_from', css_class='col-md-2'),
                Column('date_to', css_class='col-md-2'),
                Column(
                    Submit('search', 'Search', css_class='btn btn-primary'),
                    css_class='col-md-1'
                ),
            )
        )


class CancellationForm(forms.Form):
    """
    Form for booking cancellation
    """
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide reason for cancellation...'
        })
    )
    
    confirm_cancellation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, booking=None, *args, **kwargs):
        self.booking = booking
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        refund_amount = booking.refund_amount if booking else 0
        
        self.helper.layout = Layout(
            HTML(f'<div class="alert alert-warning"><strong>Refund Amount:</strong> ₹{refund_amount:.2f}</div>'),
            'cancellation_reason',
            Div(
                'confirm_cancellation',
                HTML('<label for="id_confirm_cancellation" class="form-check-label">I understand the cancellation policy and confirm cancellation</label>'),
                css_class='form-check'
            ),
            HTML('<hr>'),
            FormActions(
                Submit('cancel_booking', 'Confirm Cancellation', css_class='btn btn-danger'),
                HTML('<a href="javascript:history.back()" class="btn btn-secondary">Go Back</a>')
            )
        )