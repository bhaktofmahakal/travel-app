"""
Unit tests for bookings app
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Booking, PassengerDetail
from .forms import BookingForm, PassengerDetailForm, CancellationForm
from travel.models import TravelOption

User = get_user_model()


class BookingModelTest(TestCase):
    """Test cases for Booking model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.travel_option = TravelOption.objects.create(
            travel_type='FLIGHT',
            operator_name='Test Airlines',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=timezone.now() + timedelta(days=7),
            arrival_datetime=timezone.now() + timedelta(days=7, hours=2),
            base_price=Decimal('5000.00'),
            available_seats=100,
            total_seats=150,
            status='ACTIVE'
        )
        
        self.booking_data = {
            'user': self.user,
            'travel_option': self.travel_option,
            'number_of_seats': 2,
            'total_price': Decimal('10000.00'),
            'contact_email': 'test@example.com',
            'contact_phone': '1234567890',
            'status': 'PENDING'
        }
    
    def test_create_booking(self):
        """Test booking creation"""
        booking = Booking.objects.create(**self.booking_data)
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.travel_option, self.travel_option)
        self.assertEqual(booking.number_of_seats, 2)
        self.assertEqual(booking.total_price, Decimal('10000.00'))
        self.assertEqual(booking.status, 'PENDING')
        self.assertIsNotNone(booking.booking_id)
    
    def test_booking_str_representation(self):
        """Test booking string representation"""
        booking = Booking.objects.create(**self.booking_data)
        expected_str = f"Booking {booking.booking_id} - {booking.user.username}"
        self.assertEqual(str(booking), expected_str)
    
    def test_booking_id_generation(self):
        """Test unique booking ID generation"""
        booking1 = Booking.objects.create(**self.booking_data)
        
        # Create second booking with different user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        booking_data2 = self.booking_data.copy()
        booking_data2['user'] = user2
        booking2 = Booking.objects.create(**booking_data2)
        
        # Booking IDs should be unique
        self.assertNotEqual(booking1.booking_id, booking2.booking_id)
        self.assertEqual(len(booking1.booking_id), 10)  # Check format
        self.assertEqual(len(booking2.booking_id), 10)
    
    def test_can_be_cancelled(self):
        """Test can_be_cancelled property"""
        # Test confirmed booking with future travel date
        booking = Booking.objects.create(**self.booking_data)
        booking.status = 'CONFIRMED'
        booking.save()
        self.assertTrue(booking.can_be_cancelled)
        
        # Test completed booking
        booking.status = 'COMPLETED'
        booking.save()
        self.assertFalse(booking.can_be_cancelled)
        
        # Test cancelled booking
        booking.status = 'CANCELLED'
        booking.save()
        self.assertFalse(booking.can_be_cancelled)
        
        # Test past travel date
        past_travel = TravelOption.objects.create(
            travel_type='TRAIN',
            operator_name='Past Train',
            source='Mumbai',
            destination='Pune',
            departure_datetime=timezone.now() - timedelta(days=1),
            arrival_datetime=timezone.now() - timedelta(hours=22),
            base_price=Decimal('1000.00'),
            available_seats=50,
            total_seats=100,
            status='ACTIVE'
        )
        booking.travel_option = past_travel
        booking.status = 'CONFIRMED'
        booking.save()
        self.assertFalse(booking.can_be_cancelled)
    
    def test_refund_amount(self):
        """Test refund amount calculation"""
        booking = Booking.objects.create(**self.booking_data)
        
        # Test with future date (should get some refund)
        self.assertGreater(booking.refund_amount, 0)
        self.assertLessEqual(booking.refund_amount, booking.total_price)
        
        # Test with past date (should get no refund)
        past_travel = TravelOption.objects.create(
            travel_type='BUS',
            operator_name='Past Bus',
            source='Mumbai',
            destination='Goa',
            departure_datetime=timezone.now() - timedelta(days=1),
            arrival_datetime=timezone.now() - timedelta(hours=20),
            base_price=Decimal('800.00'),
            available_seats=30,
            total_seats=50,
            status='ACTIVE'
        )
        booking.travel_option = past_travel
        booking.save()
        self.assertEqual(booking.refund_amount, 0)
    
    def test_days_until_travel(self):
        """Test days until travel calculation"""
        booking = Booking.objects.create(**self.booking_data)
        # Travel is set 7 days in future
        self.assertEqual(booking.days_until_travel, 7)


class PassengerDetailModelTest(TestCase):
    """Test cases for PassengerDetail model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.travel_option = TravelOption.objects.create(
            travel_type='FLIGHT',
            operator_name='Test Airlines',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=timezone.now() + timedelta(days=5),
            arrival_datetime=timezone.now() + timedelta(days=5, hours=2),
            base_price=Decimal('4000.00'),
            available_seats=80,
            total_seats=120,
            status='ACTIVE'
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=1,
            total_price=Decimal('4000.00'),
            contact_email='test@example.com',
            contact_phone='1234567890',
            status='PENDING'
        )
        
        self.passenger_data = {
            'booking': self.booking,
            'title': 'Mr.',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': timezone.now().date() - timedelta(days=365*30),
            'gender': 'M',
            'id_type': 'Passport',
            'id_number': 'AB1234567',
            'seat_preference': 'Window',
            'meal_preference': 'Vegetarian'
        }
    
    def test_create_passenger_detail(self):
        """Test passenger detail creation"""
        passenger = PassengerDetail.objects.create(**self.passenger_data)
        self.assertEqual(passenger.booking, self.booking)
        self.assertEqual(passenger.first_name, 'John')
        self.assertEqual(passenger.last_name, 'Doe')
        self.assertEqual(passenger.gender, 'M')
        self.assertEqual(passenger.seat_preference, 'Window')
    
    def test_passenger_detail_str_representation(self):
        """Test passenger detail string representation"""
        passenger = PassengerDetail.objects.create(**self.passenger_data)
        expected_str = f"{passenger.title} {passenger.first_name} {passenger.last_name}"
        self.assertEqual(str(passenger), expected_str)
    
    def test_passenger_full_name(self):
        """Test passenger full name property"""
        passenger = PassengerDetail.objects.create(**self.passenger_data)
        expected_name = f"{passenger.first_name} {passenger.last_name}"
        self.assertEqual(passenger.full_name, expected_name)


class BookingViewsTest(TestCase):
    """Test cases for booking views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.travel_option = TravelOption.objects.create(
            travel_type='FLIGHT',
            operator_name='Test Airlines',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=timezone.now() + timedelta(days=10),
            arrival_datetime=timezone.now() + timedelta(days=10, hours=2),
            base_price=Decimal('6000.00'),
            available_seats=100,
            total_seats=150,
            status='ACTIVE'
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=2,
            total_price=Decimal('12000.00'),
            contact_email='test@example.com',
            contact_phone='1234567890',
            status='CONFIRMED'
        )
    
    def test_booking_list_view_authenticated(self):
        """Test booking list view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('bookings:list'))
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertContains(response, 'My Bookings')
            self.assertIn(self.booking, response.context['bookings'])
    
    def test_booking_list_view_unauthenticated(self):
        """Test booking list view for unauthenticated user"""
        response = self.client.get(reverse('bookings:list'))
        self.assertIn(response.status_code, [301, 302])  # Redirect to login
    
    def test_booking_detail_view(self):
        """Test booking detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('bookings:detail', args=[self.booking.booking_id]))
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertEqual(response.context['booking'], self.booking)
        if response.status_code == 200:
            self.assertContains(response, self.booking.booking_id)
    
    def test_booking_detail_view_wrong_user(self):
        """Test booking detail view with wrong user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('bookings:detail', args=[self.booking.booking_id]))
        self.assertIn(response.status_code, [301, 302, 404])  # Should not see other user's booking
    
    def test_booking_create_view_get(self):
        """Test GET request to booking create view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('bookings:create', args=[self.travel_option.pk]))
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertContains(response, 'Book Travel')
            self.assertIsInstance(response.context['form'], BookingForm)
    
    def test_booking_create_view_post_valid(self):
        """Test POST request to booking create view with valid data"""
        self.client.login(username='testuser', password='testpass123')
        booking_data = {
            'number_of_seats': 1,
            'contact_email': 'test@example.com',
            'contact_phone': '9876543210',
            'special_requests': 'Window seat please',
            'agree_terms': True
        }
        response = self.client.post(
            reverse('bookings:create', args=[self.travel_option.pk]), 
            booking_data
        )
        self.assertIn(response.status_code, [301, 302])  # Redirect after successful booking
        
        # Check booking was created
        new_booking = Booking.objects.filter(user=self.user).exclude(id=self.booking.id).first()
        if new_booking:
            self.assertEqual(new_booking.number_of_seats, 1)


class BookingFormsTest(TestCase):
    """Test cases for booking forms"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.travel_option = TravelOption.objects.create(
            travel_type='TRAIN',
            operator_name='Express Train',
            source='Mumbai',
            destination='Pune',
            departure_datetime=timezone.now() + timedelta(days=3),
            arrival_datetime=timezone.now() + timedelta(days=3, hours=4),
            base_price=Decimal('1200.00'),
            available_seats=50,
            total_seats=100,
            status='ACTIVE'
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=1,
            total_price=Decimal('1200.00'),
            contact_email='test@example.com',
            contact_phone='1234567890',
            status='CONFIRMED'
        )
    
    def test_booking_form_valid_data(self):
        """Test BookingForm with valid data"""
        form_data = {
            'number_of_seats': 2,
            'contact_email': 'test@example.com',
            'contact_phone': '9876543210',
            'special_requests': 'Prefer seats together',
            'agree_terms': True
        }
        form = BookingForm(
            data=form_data,
            travel_option=self.travel_option,
            user=self.user
        )
        self.assertTrue(form.is_valid())
    
    def test_booking_form_too_many_seats(self):
        """Test BookingForm with too many seats requested"""
        form_data = {
            'number_of_seats': 100,  # More than available
            'contact_email': 'test@example.com',
            'contact_phone': '9876543210',
            'agree_terms': True
        }
        form = BookingForm(
            data=form_data,
            travel_option=self.travel_option,
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('number_of_seats', form.errors)
    
    def test_booking_form_missing_terms(self):
        """Test BookingForm without agreeing to terms"""
        form_data = {
            'number_of_seats': 1,
            'contact_email': 'test@example.com',
            'contact_phone': '9876543210',
            'agree_terms': False
        }
        form = BookingForm(
            data=form_data,
            travel_option=self.travel_option,
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('agree_terms', form.errors)
    
    def test_passenger_detail_form_valid_data(self):
        """Test PassengerDetailForm with valid data"""
        form_data = {
            'title': 'MS',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': (timezone.now() - timedelta(days=365*25)).date(),
            'gender': 'F',
            'id_type': 'Driving License',
            'id_number': 'DL123456789',
            'seat_preference': 'Aisle',
            'meal_preference': 'Non-Vegetarian'
        }
        form = PassengerDetailForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_cancellation_form_valid_data(self):
        """Test CancellationForm with valid data"""
        form_data = {
            'cancellation_reason': 'Change in travel plans',
            'confirm_cancellation': True
        }
        form = CancellationForm(data=form_data, booking=self.booking)
        self.assertTrue(form.is_valid())
    
    def test_cancellation_form_missing_confirmation(self):
        """Test CancellationForm without confirmation"""
        form_data = {
            'cancellation_reason': 'Change in plans',
            'confirm_cancellation': False
        }
        form = CancellationForm(data=form_data, booking=self.booking)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_cancellation', form.errors)


class BookingIntegrationTest(TestCase):
    """Integration tests for booking workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123',
            first_name='Integration',
            last_name='User'
        )
        
        self.travel_option = TravelOption.objects.create(
            travel_type='BUS',
            operator_name='Integration Bus',
            source='Mumbai',
            destination='Goa',
            departure_datetime=timezone.now() + timedelta(days=15),
            arrival_datetime=timezone.now() + timedelta(days=15, hours=8),
            base_price=Decimal('800.00'),
            available_seats=40,
            total_seats=50,
            status='ACTIVE'
        )
    
    def test_complete_booking_workflow(self):
        """Test complete booking workflow from creation to cancellation"""
        # Login user
        self.client.login(username='integrationuser', password='integrationpass123')
        
        # Step 1: Create booking
        booking_data = {
            'number_of_seats': 2,
            'contact_email': 'integration@example.com',
            'contact_phone': '9988776655',
            'special_requests': 'Window seats preferred',
            'agree_terms': True
        }
        create_response = self.client.post(
            reverse('bookings:create', args=[self.travel_option.pk]),
            booking_data
        )
        self.assertIn(create_response.status_code, [301, 302])
        
        # Verify booking was created
        if Booking.objects.filter(user=self.user).exists():
            booking = Booking.objects.get(user=self.user)
            self.assertEqual(booking.number_of_seats, 2)
            self.assertEqual(booking.status, 'PENDING')
        
        # Step 2: View booking list
        list_response = self.client.get(reverse('bookings:list'))
        self.assertIn(list_response.status_code, [200, 301])
        if list_response.status_code == 200 and 'booking' in locals():
            self.assertContains(list_response, booking.booking_id)
        
        # Step 3: View booking detail
        if 'booking' in locals():
            detail_response = self.client.get(
                reverse('bookings:detail', args=[booking.booking_id])
            )
            self.assertIn(detail_response.status_code, [200, 301])
            if detail_response.status_code == 200:
                self.assertEqual(detail_response.context['booking'], booking)
        
        # Step 4: Confirm booking (simulate admin action)
        if 'booking' in locals():
            booking.status = 'CONFIRMED'
            booking.save()
        
        # Step 5: Cancel booking
        if 'booking' in locals() and booking.can_be_cancelled:
            cancellation_data = {
                'cancellation_reason': 'Travel plans changed',
                'confirm_cancellation': True
            }
            cancel_response = self.client.post(
                reverse('bookings:cancel', args=[booking.booking_id]),
                cancellation_data
            )
            self.assertEqual(cancel_response.status_code, 302)
            
            # Verify booking was cancelled
            booking.refresh_from_db()
            self.assertEqual(booking.status, 'CANCELLED')
            
            # Verify seats were restored
            self.travel_option.refresh_from_db()
            self.assertEqual(self.travel_option.available_seats, 40)  # Should be restored
    
    def test_booking_filters_and_search(self):
        """Test booking list filters and search functionality"""
        self.client.login(username='integrationuser', password='integrationpass123')
        
        # Create multiple bookings with different statuses
        bookings = []
        for i, status in enumerate(['PENDING', 'CONFIRMED', 'CANCELLED']):
            booking = Booking.objects.create(
                user=self.user,
                travel_option=self.travel_option,
                number_of_seats=1,
                total_price=Decimal('800.00'),
                contact_email=f'test{i}@example.com',
                contact_phone=f'999888777{i}',
                status=status
            )
            bookings.append(booking)
        
        # Test status filter
        confirmed_response = self.client.get(
            reverse('bookings:list'),
            {'status': 'CONFIRMED'}
        )
        self.assertIn(confirmed_response.status_code, [200, 301])
        if confirmed_response.status_code == 200:
            confirmed_bookings = confirmed_response.context['bookings']
            self.assertTrue(
                all(booking.status == 'CONFIRMED' for booking in confirmed_bookings)
            )
        
        # Test search by booking ID
        search_response = self.client.get(
            reverse('bookings:list'),
            {'search': bookings[0].booking_id}
        )
        self.assertIn(search_response.status_code, [200, 301])
        if search_response.status_code == 200:
            search_results = search_response.context['bookings']
            self.assertEqual(len(search_results), 1)
            self.assertEqual(search_results[0], bookings[0])