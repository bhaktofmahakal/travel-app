"""
Forms for Travel Options Search and Management
"""

from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import FormActions
from .models import TravelOption, TravelOperator


class TravelSearchForm(forms.Form):
    """
    Form for searching travel options
    """
    TRAVEL_TYPE_CHOICES = [
        ('', 'All Types'),
        ('FLIGHT', 'Flight'),
        ('TRAIN', 'Train'),
        ('BUS', 'Bus'),
    ]
    
    SORT_CHOICES = [
        ('departure_datetime', 'Departure Time'),
        ('base_price', 'Price (Low to High)'),
        ('-base_price', 'Price (High to Low)'),
        ('duration', 'Duration'),
        ('-available_seats', 'Availability'),
    ]
    
    # Search criteria
    travel_type = forms.ChoiceField(
        choices=TRAVEL_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    source = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'From (City/Airport)',
            'class': 'form-control',
            'list': 'source_datalist'
        })
    )
    destination = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'To (City/Airport)',
            'class': 'form-control',
            'list': 'destination_datalist'
        })
    )
    departure_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat()
        })
    )
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    # Filters
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'form-control'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'form-control'
        })
    )
    min_seats = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Passengers',
            'class': 'form-control'
        })
    )
    
    # Sorting
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='departure_datetime',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'travel-search-form'
        
        self.helper.layout = Layout(
            Div(
                Row(
                    Column('travel_type', css_class='col-md-3'),
                    Column('source', css_class='col-md-3'),
                    Column('destination', css_class='col-md-3'),
                    Column('departure_date', css_class='col-md-3'),
                ),
                css_class='row mb-3'
            ),
            Div(
                Row(
                    Column('return_date', css_class='col-md-3'),
                    Column('min_price', css_class='col-md-2'),
                    Column('max_price', css_class='col-md-2'),
                    Column('min_seats', css_class='col-md-2'),
                    Column('sort_by', css_class='col-md-3'),
                ),
                css_class='row mb-3'
            ),
            FormActions(
                Submit('search', 'Search Travel Options', css_class='btn btn-primary btn-lg'),
                HTML('<button type="button" class="btn btn-outline-secondary" onclick="clearForm()">Clear</button>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        return_date = cleaned_data.get('return_date')
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        # Validate date range
        if departure_date and departure_date < timezone.now().date():
            raise forms.ValidationError("Departure date cannot be in the past.")
        
        if return_date and departure_date and return_date < departure_date:
            raise forms.ValidationError("Return date must be after departure date.")
        
        # Validate price range
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price.")
        
        return cleaned_data


class TravelOptionForm(forms.ModelForm):
    """
    Form for creating/updating travel options (Admin use)
    """
    departure_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    arrival_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = TravelOption
        fields = [
            'travel_type', 'operator_name', 'source', 'destination',
            'source_code', 'destination_code', 'departure_datetime',
            'arrival_datetime', 'base_price', 'available_seats',
            'total_seats', 'description', 'baggage_allowance',
            'cancellation_policy', 'status', 'is_featured'
        ]
        widgets = {
            'travel_type': forms.Select(attrs={'class': 'form-select'}),
            'operator_name': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'source_code': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_code': forms.TextInput(attrs={'class': 'form-control'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'baggage_allowance': forms.TextInput(attrs={'class': 'form-control'}),
            'cancellation_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            HTML('<h4>Travel Information</h4><hr>'),
            Row(
                Column('travel_type', css_class='col-md-4'),
                Column('operator_name', css_class='col-md-8'),
            ),
            Row(
                Column('source', css_class='col-md-5'),
                Column('source_code', css_class='col-md-2'),
                Column('destination', css_class='col-md-5'),
            ),
            'destination_code',
            HTML('<h4>Schedule</h4><hr>'),
            Row(
                Column('departure_datetime', css_class='col-md-6'),
                Column('arrival_datetime', css_class='col-md-6'),
            ),
            HTML('<h4>Pricing & Capacity</h4><hr>'),
            Row(
                Column('base_price', css_class='col-md-4'),
                Column('available_seats', css_class='col-md-4'),
                Column('total_seats', css_class='col-md-4'),
            ),
            HTML('<h4>Additional Information</h4><hr>'),
            'description',
            'baggage_allowance',
            'cancellation_policy',
            Row(
                Column('status', css_class='col-md-6'),
                Column('is_featured', css_class='col-md-6'),
            ),
            HTML('<hr>'),
            FormActions(
                Submit('save', 'Save Travel Option', css_class='btn btn-primary'),
                HTML('<a href="{% url "travel:list" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        departure_datetime = cleaned_data.get('departure_datetime')
        arrival_datetime = cleaned_data.get('arrival_datetime')
        available_seats = cleaned_data.get('available_seats')
        total_seats = cleaned_data.get('total_seats')
        
        # Validate datetime
        if departure_datetime and arrival_datetime:
            if departure_datetime >= arrival_datetime:
                raise forms.ValidationError("Arrival time must be after departure time.")
        
        # Validate seats
        if available_seats and total_seats:
            if available_seats > total_seats:
                raise forms.ValidationError("Available seats cannot exceed total seats.")
        
        return cleaned_data


class QuickSearchForm(forms.Form):
    """
    Simplified search form for homepage
    """
    source = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'From',
            'class': 'form-control form-control-lg'
        })
    )
    destination = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'To',
            'class': 'form-control form-control-lg'
        })
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-lg',
            'min': timezone.now().date().isoformat()
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_action = '/travel/search/'
        self.helper.form_class = 'quick-search-form'
        
        self.helper.layout = Layout(
            Row(
                Column('source', css_class='col-md-4'),
                Column('destination', css_class='col-md-4'),
                Column('departure_date', css_class='col-md-2'),
                Column(
                    Submit('search', 'Search', css_class='btn btn-primary btn-lg'),
                    css_class='col-md-2'
                ),
            )
        )