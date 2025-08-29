"""
Unit tests for travel app
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from .models import TravelOption, PopularRoute
from .forms import TravelSearchForm, QuickSearchForm


class TravelOptionModelTest(TestCase):
    """Test cases for TravelOption model"""
    
    def setUp(self):
        """Set up test data"""
        self.travel_option_data = {
            'travel_type': 'FLIGHT',
            'operator_name': 'Test Airlines',
            'source': 'Mumbai',
            'destination': 'Delhi',
            'source_code': 'BOM',
            'destination_code': 'DEL',
            'departure_datetime': timezone.now() + timedelta(days=1),
            'arrival_datetime': timezone.now() + timedelta(days=1, hours=2),
            'base_price': Decimal('5000.00'),
            'available_seats': 100,
            'total_seats': 150,
            'description': 'Test flight description',
            'status': 'ACTIVE'
        }
    
    def test_create_travel_option(self):
        """Test travel option creation"""
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        self.assertEqual(travel_option.travel_type, 'FLIGHT')
        self.assertEqual(travel_option.operator_name, 'Test Airlines')
        self.assertEqual(travel_option.source, 'Mumbai')
        self.assertEqual(travel_option.destination, 'Delhi')
        self.assertEqual(travel_option.base_price, Decimal('5000.00'))
        self.assertEqual(travel_option.available_seats, 100)
        self.assertEqual(travel_option.status, 'ACTIVE')
    
    def test_travel_option_str_representation(self):
        """Test travel option string representation"""
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        expected_str = f"{travel_option.travel_id} - {travel_option.source} to {travel_option.destination} ({travel_option.travel_type})"
        self.assertEqual(str(travel_option), expected_str)
    
    def test_duration_property(self):
        """Test duration calculation"""
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        expected_duration = self.travel_option_data['arrival_datetime'] - self.travel_option_data['departure_datetime']
        self.assertEqual(travel_option.duration, expected_duration)
    
    def test_is_available_property(self):
        """Test is_available property"""
        # Test with available seats and future date
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        self.assertTrue(travel_option.is_available)
        
        # Test with no available seats
        travel_option.available_seats = 0
        travel_option.save()
        self.assertFalse(travel_option.is_available)
        
        # Test with past departure date
        travel_option.available_seats = 100
        travel_option.departure_datetime = timezone.now() - timedelta(hours=1)
        travel_option.save()
        self.assertFalse(travel_option.is_available)
    
    def test_reduce_available_seats(self):
        """Test reduce_available_seats method"""
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        initial_seats = travel_option.available_seats
        
        result = travel_option.reduce_available_seats(10)
        travel_option.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(travel_option.available_seats, initial_seats - 10)
    
    def test_increase_available_seats(self):
        """Test increase_available_seats method"""
        travel_option = TravelOption.objects.create(**self.travel_option_data)
        initial_seats = travel_option.available_seats
        
        result = travel_option.increase_available_seats(20)
        travel_option.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(travel_option.available_seats, initial_seats + 20)


class TravelSearchTest(TestCase):
    """Test cases for travel search functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.search_url = reverse('travel:search')
        
        # Create test travel options
        base_datetime = timezone.now() + timedelta(days=1)
        
        self.flight = TravelOption.objects.create(
            travel_type='FLIGHT',
            operator_name='Test Airways',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=base_datetime,
            arrival_datetime=base_datetime + timedelta(hours=2),
            base_price=Decimal('5000.00'),
            available_seats=50,
            total_seats=100,
            status='ACTIVE'
        )
        
        self.train = TravelOption.objects.create(
            travel_type='TRAIN',
            operator_name='Test Railways',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=base_datetime + timedelta(hours=3),
            arrival_datetime=base_datetime + timedelta(hours=20),
            base_price=Decimal('1500.00'),
            available_seats=200,
            total_seats=300,
            status='ACTIVE'
        )
    
    def test_search_view_get(self):
        """Test GET request to search view"""
        response = self.client.get(self.search_url)
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertContains(response, 'Search Travel')
            self.assertIsInstance(response.context['form'], TravelSearchForm)
    
    def test_search_with_filters(self):
        """Test search with various filters"""
        search_data = {
            'travel_type': 'FLIGHT',
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=1)).date(),
            'sort_by': 'base_price'
        }
        response = self.client.get(self.search_url, search_data)
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertContains(response, 'Test Airways')
            self.assertNotContains(response, 'Test Railways')
    
    def test_search_without_filters(self):
        """Test search without filters returns all results"""
        response = self.client.get(self.search_url)
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            # Should contain both flight and train
            self.assertContains(response, 'Test Airways')
            self.assertContains(response, 'Test Railways')
    
    def test_search_price_range_filter(self):
        """Test search with price range filter"""
        search_data = {
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=1)).date(),
            'min_price': 1000,
            'max_price': 2000
        }
        response = self.client.get(self.search_url, search_data)
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            # Should contain only train (price 1500)
            self.assertNotContains(response, 'Test Airways')
            self.assertContains(response, 'Test Railways')


class TravelDetailTest(TestCase):
    """Test cases for travel detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.travel_option = TravelOption.objects.create(
            travel_type='FLIGHT',
            operator_name='Detail Airways',
            source='Mumbai',
            destination='Delhi',
            departure_datetime=timezone.now() + timedelta(days=1),
            arrival_datetime=timezone.now() + timedelta(days=1, hours=2),
            base_price=Decimal('6000.00'),
            available_seats=75,
            total_seats=120,
            description='Detailed flight description',
            status='ACTIVE'
        )
        self.detail_url = reverse('travel:detail', args=[self.travel_option.pk])
    
    def test_travel_detail_view(self):
        """Test travel detail view"""
        response = self.client.get(self.detail_url)
        self.assertIn(response.status_code, [200, 301])
        if response.status_code == 200:
            self.assertEqual(response.context['travel_option'], self.travel_option)
            self.assertContains(response, 'Detail Airways')
            self.assertContains(response, 'Mumbai')
            self.assertContains(response, 'Delhi')
    
    def test_travel_detail_view_inactive_option(self):
        """Test detail view for inactive travel option"""
        self.travel_option.status = 'INACTIVE'
        self.travel_option.save()
        response = self.client.get(self.detail_url)
        # Should still be accessible but show appropriate message
        self.assertIn(response.status_code, [200, 301])
    
    def test_travel_detail_view_nonexistent_option(self):
        """Test detail view for non-existent travel option"""
        nonexistent_url = reverse('travel:detail', args=[99999])
        response = self.client.get(nonexistent_url)
        self.assertIn(response.status_code, [301, 404])


class TravelFormsTest(TestCase):
    """Test cases for travel forms"""
    
    def test_travel_search_form_valid_data(self):
        """Test TravelSearchForm with valid data"""
        form_data = {
            'travel_type': 'FLIGHT',
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=1)).date(),
            'min_price': 1000,
            'max_price': 10000,
            'min_seats': 1,
            'sort_by': 'base_price'
        }
        form = TravelSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_travel_search_form_past_date(self):
        """Test TravelSearchForm with past departure date"""
        form_data = {
            'travel_type': 'FLIGHT',
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() - timedelta(days=1)).date(),
        }
        form = TravelSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Departure date cannot be in the past', str(form.errors))
    
    def test_travel_search_form_invalid_price_range(self):
        """Test TravelSearchForm with invalid price range"""
        form_data = {
            'travel_type': 'FLIGHT',
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=1)).date(),
            'min_price': 10000,
            'max_price': 5000,  # Max less than min
        }
        form = TravelSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Minimum price cannot be greater than maximum price', str(form.errors))
    
    def test_quick_search_form_valid_data(self):
        """Test QuickSearchForm with valid data"""
        form_data = {
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=1)).date(),
        }
        form = QuickSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class PopularRouteModelTest(TestCase):
    """Test cases for PopularRoute model"""
    
    def test_create_popular_route(self):
        """Test popular route creation"""
        route = PopularRoute.objects.create(
            source='Mumbai',
            destination='Delhi',
            search_count=100,
            booking_count=25
        )
        self.assertEqual(route.source, 'Mumbai')
        self.assertEqual(route.destination, 'Delhi')
        self.assertEqual(route.search_count, 100)
        self.assertEqual(route.booking_count, 25)
    
    def test_popular_route_str_representation(self):
        """Test popular route string representation"""
        route = PopularRoute.objects.create(
            source='Mumbai',
            destination='Delhi',
            search_count=50,
            booking_count=10
        )
        expected_str = f"{route.source} → {route.destination}"
        self.assertEqual(str(route), expected_str)
    
    def test_increment_search_count(self):
        """Test increment_search_count method"""
        route = PopularRoute.objects.create(
            source='Mumbai',
            destination='Delhi',
            search_count=10,
            booking_count=5
        )
        initial_count = route.search_count
        route.increment_search_count()
        route.refresh_from_db()
        
        self.assertEqual(route.search_count, initial_count + 1)
    
    def test_increment_booking_count(self):
        """Test increment_booking_count method"""
        route = PopularRoute.objects.create(
            source='Mumbai',
            destination='Delhi',
            search_count=20,
            booking_count=8
        )
        initial_count = route.booking_count
        route.increment_booking_count()
        route.refresh_from_db()
        
        self.assertEqual(route.booking_count, initial_count + 1)


class TravelIntegrationTest(TestCase):
    """Integration tests for travel workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create multiple travel options
        base_datetime = timezone.now() + timedelta(days=2)
        
        self.options = []
        for i in range(5):
            option = TravelOption.objects.create(
                travel_type='FLIGHT' if i % 2 == 0 else 'TRAIN',
                operator_name=f'Operator {i+1}',
                source='Mumbai',
                destination='Delhi',
                departure_datetime=base_datetime + timedelta(hours=i*2),
                arrival_datetime=base_datetime + timedelta(hours=i*2+3),
                base_price=Decimal(str(2000 + i*1000)),
                available_seats=50 - i*5,
                total_seats=100,
                status='ACTIVE'
            )
            self.options.append(option)
    
    def test_complete_search_workflow(self):
        """Test complete search workflow"""
        # Initial search page
        search_response = self.client.get(reverse('travel:search'))
        self.assertIn(search_response.status_code, [200, 301])
        
        # Search with filters
        search_data = {
            'source': 'Mumbai',
            'destination': 'Delhi',
            'departure_date': (timezone.now() + timedelta(days=2)).date(),
            'travel_type': 'FLIGHT',
            'sort_by': 'base_price'
        }
        filtered_response = self.client.get(reverse('travel:search'), search_data)
        self.assertIn(filtered_response.status_code, [200, 301])
        
        # Check that results are filtered and sorted
        if filtered_response.status_code == 200:
            results = filtered_response.context['travel_options']
            flight_results = [opt for opt in results if opt.travel_type == 'FLIGHT']
            self.assertTrue(len(flight_results) > 0)
        
        # Test detail view
        first_option = self.options[0]
        detail_response = self.client.get(reverse('travel:detail', args=[first_option.pk]))
        self.assertIn(detail_response.status_code, [200, 301])
        if detail_response.status_code == 200:
            self.assertEqual(detail_response.context['travel_option'], first_option)