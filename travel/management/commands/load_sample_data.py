"""
Management command to load sample travel data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from travel.models import TravelOption, TravelOperator, PopularRoute


class Command(BaseCommand):
    help = 'Load sample travel data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of travel options to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            TravelOption.objects.all().delete()
            TravelOperator.objects.all().delete()
            PopularRoute.objects.all().delete()

        # Create operators
        self.create_operators()
        
        # Create travel options
        self.create_travel_options(options['count'])
        
        # Create popular routes
        self.create_popular_routes()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {options["count"]} travel options')
        )

    def create_operators(self):
        """Create sample travel operators"""
        operators_data = [
            # Airlines
            ('Air India', 'FLIGHT', 'AI'),
            ('IndiGo', 'FLIGHT', '6E'),
            ('SpiceJet', 'FLIGHT', 'SG'),
            ('Vistara', 'FLIGHT', 'UK'),
            ('GoAir', 'FLIGHT', 'G8'),
            
            # Railways
            ('Indian Railways', 'TRAIN', 'IR'),
            ('Rajdhani Express', 'TRAIN', 'RAJ'),
            ('Shatabdi Express', 'TRAIN', 'SHT'),
            ('Duronto Express', 'TRAIN', 'DUR'),
            
            # Bus Operators
            ('Redbus', 'BUS', 'RB'),
            ('Volvo', 'BUS', 'VO'),
            ('KSRTC', 'BUS', 'KS'),
            ('APSRTC', 'BUS', 'AP'),
            ('SRS Travels', 'BUS', 'SRS'),
            ('VRL Travels', 'BUS', 'VRL'),
        ]

        for name, operator_type, code in operators_data:
            TravelOperator.objects.get_or_create(
                name=name,
                defaults={
                    'operator_type': operator_type,
                    'code': code,
                    'contact_email': f'info@{code.lower()}.com',
                    'contact_phone': f'+91-9876543{random.randint(100, 999)}',
                    'website': f'https://{code.lower()}.com',
                    'is_active': True,
                }
            )

        self.stdout.write('Created travel operators')

    def create_travel_options(self, count):
        """Create sample travel options"""
        # Indian cities data
        cities = [
            ('Mumbai', 'BOM'), ('Delhi', 'DEL'), ('Bangalore', 'BLR'),
            ('Chennai', 'MAA'), ('Kolkata', 'CCU'), ('Hyderabad', 'HYD'),
            ('Pune', 'PNQ'), ('Ahmedabad', 'AMD'), ('Jaipur', 'JAI'),
            ('Kochi', 'COK'), ('Goa', 'GOI'), ('Lucknow', 'LKO'),
            ('Chandigarh', 'IXC'), ('Bhopal', 'BHO'), ('Coimbatore', 'CJB'),
            ('Indore', 'IDR'), ('Nagpur', 'NAG'), ('Vadodara', 'BDQ'),
            ('Visakhapatnam', 'VTZ'), ('Bhubaneswar', 'BBI'),
        ]

        travel_types = ['FLIGHT', 'TRAIN', 'BUS']
        operators = list(TravelOperator.objects.all())

        for i in range(count):
            # Random source and destination
            source, source_code = random.choice(cities)
            destination, dest_code = random.choice(cities)
            
            # Ensure different source and destination
            while source == destination:
                destination, dest_code = random.choice(cities)

            # Random travel type and corresponding operator
            travel_type = random.choice(travel_types)
            operator = random.choice([op for op in operators if op.operator_type == travel_type])

            # Random dates (next 90 days)
            departure_date = timezone.now() + timedelta(
                days=random.randint(1, 90),
                hours=random.randint(6, 22),
                minutes=random.choice([0, 30])
            )
            
            # Flight duration: 1-5 hours, Train: 3-24 hours, Bus: 4-15 hours
            if travel_type == 'FLIGHT':
                duration_hours = random.randint(1, 5)
            elif travel_type == 'TRAIN':
                duration_hours = random.randint(3, 24)
            else:  # BUS
                duration_hours = random.randint(4, 15)
            
            arrival_date = departure_date + timedelta(hours=duration_hours)

            # Random pricing based on travel type
            if travel_type == 'FLIGHT':
                base_price = random.randint(3000, 15000)
            elif travel_type == 'TRAIN':
                base_price = random.randint(500, 3000)
            else:  # BUS
                base_price = random.randint(400, 2000)

            # Random seat configuration
            if travel_type == 'FLIGHT':
                total_seats = random.choice([150, 180, 200, 250])
            elif travel_type == 'TRAIN':
                total_seats = random.choice([72, 64, 48])  # Different classes
            else:  # BUS
                total_seats = random.choice([32, 40, 49, 56])

            available_seats = random.randint(0, total_seats)

            # Create travel option
            TravelOption.objects.create(
                travel_id=f'{operator.code}{random.randint(100, 999)}',
                travel_type=travel_type,
                operator_name=operator.name,
                source=source,
                destination=destination,
                source_code=source_code,
                destination_code=dest_code,
                departure_datetime=departure_date,
                arrival_datetime=arrival_date,
                base_price=base_price,
                available_seats=available_seats,
                total_seats=total_seats,
                description=self.get_description(travel_type, operator.name),
                amenities=self.get_amenities(travel_type),
                baggage_allowance=self.get_baggage_allowance(travel_type),
                cancellation_policy=self.get_cancellation_policy(),
                status='ACTIVE',
                is_featured=random.choice([True, False]) if random.random() < 0.2 else False,
            )

        self.stdout.write(f'Created {count} travel options')

    def create_popular_routes(self):
        """Create popular routes based on created travel options"""
        routes_data = [
            ('Mumbai', 'Delhi', 150, 45),
            ('Bangalore', 'Chennai', 120, 38),
            ('Delhi', 'Mumbai', 145, 42),
            ('Chennai', 'Bangalore', 115, 35),
            ('Hyderabad', 'Mumbai', 95, 28),
            ('Pune', 'Bangalore', 85, 25),
            ('Kolkata', 'Delhi', 78, 22),
            ('Mumbai', 'Goa', 92, 31),
            ('Delhi', 'Jaipur', 67, 20),
            ('Chennai', 'Kochi', 58, 18),
        ]

        for source, destination, searches, bookings in routes_data:
            PopularRoute.objects.get_or_create(
                source=source,
                destination=destination,
                defaults={
                    'search_count': searches,
                    'booking_count': bookings,
                }
            )

        self.stdout.write('Created popular routes')

    def get_description(self, travel_type, operator_name):
        """Generate description based on travel type"""
        descriptions = {
            'FLIGHT': f'Comfortable air travel with {operator_name}. Enjoy in-flight entertainment and refreshments.',
            'TRAIN': f'Reliable train service by {operator_name}. Clean coaches with modern amenities.',
            'BUS': f'Safe and comfortable bus journey with {operator_name}. AC coaches with reclining seats.',
        }
        return descriptions.get(travel_type, 'Comfortable travel experience.')

    def get_amenities(self, travel_type):
        """Generate amenities based on travel type"""
        amenities = {
            'FLIGHT': 'In-flight entertainment, Meals, WiFi, Baggage allowance',
            'TRAIN': 'AC coaches, Clean restrooms, Pantry service, Bedding',
            'BUS': 'AC, Reclining seats, Entertainment system, USB charging',
        }
        return amenities.get(travel_type, 'Standard amenities')

    def get_baggage_allowance(self, travel_type):
        """Generate baggage allowance based on travel type"""
        baggage = {
            'FLIGHT': '7kg cabin + 15kg check-in',
            'TRAIN': '40kg personal luggage',
            'BUS': '25kg under storage',
        }
        return baggage.get(travel_type, 'Standard baggage allowance')

    def get_cancellation_policy(self):
        """Generate cancellation policy"""
        policies = [
            'Free cancellation up to 24 hours before departure',
            'Cancellation charges: 25% of ticket price before 24 hours',
            'Full refund for cancellation before 48 hours, 50% after that',
            'Non-refundable. Date change allowed with charges',
        ]
        return random.choice(policies)