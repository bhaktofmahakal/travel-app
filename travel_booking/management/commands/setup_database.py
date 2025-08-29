"""
Management command to setup database with sample data
Usage: python manage.py setup_database
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import sys

from travel.models import TravelOption
from bookings.models import Booking

User = get_user_model()


class Command(BaseCommand):
    help = 'Sets up the database with migrations, superuser, and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation',
        )
        parser.add_argument(
            '--skip-sample-data',
            action='store_true',
            help='Skip sample data creation',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Setting up Travel Booking Database...\n')
        )

        # Step 1: Run migrations
        self.stdout.write('📦 Running database migrations...')
        try:
            call_command('makemigrations', verbosity=0)
            call_command('migrate', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✅ Database migrations completed')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {str(e)}')
            )
            return

        # Step 2: Create superuser
        if not options['skip_superuser']:
            self.stdout.write('\n👤 Creating superuser...')
            if User.objects.filter(is_superuser=True).exists():
                self.stdout.write(
                    self.style.WARNING('⚠️  Superuser already exists, skipping...')
                )
            else:
                try:
                    call_command(
                        'createsuperuser',
                        username='admin',
                        email='admin@travelbooking.com',
                        interactive=False,
                    )
                    # Set password
                    admin_user = User.objects.get(username='admin')
                    admin_user.set_password('admin123')  # Change in production
                    admin_user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS('✅ Superuser created (admin/admin123)')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Could not create superuser: {str(e)}')
                    )

        # Step 3: Create sample data
        if not options['skip_sample_data']:
            self.stdout.write('\n📊 Creating sample data...')
            self.create_sample_data()

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Database setup completed successfully!')
        )
        self.stdout.write('\n📌 Next steps:')
        self.stdout.write('   1. Run: python manage.py runserver')
        self.stdout.write('   2. Visit: http://127.0.0.1:8000/')
        self.stdout.write('   3. Admin: http://127.0.0.1:8000/admin/')

    def create_sample_data(self):
        """Create sample travel options and users"""
        
        # Create sample users
        sample_users = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '9876543210'
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone_number': '9876543211'
            }
        ]

        for user_data in sample_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='password123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone_number=user_data['phone_number']
                )
                self.stdout.write(f'   👤 Created user: {user.username}')

        # Create sample travel options
        base_datetime = timezone.now() + timedelta(days=1)
        
        sample_travels = [
            {
                'travel_type': 'FLIGHT',
                'operator_name': 'SkyWings Airlines',
                'travel_id': 'SW101',
                'source': 'Mumbai',
                'destination': 'Delhi',
                'departure_datetime': base_datetime,
                'arrival_datetime': base_datetime + timedelta(hours=2),
                'base_price': Decimal('4500.00'),
                'available_seats': 45,
                'total_seats': 50
            },
            {
                'travel_type': 'TRAIN',
                'operator_name': 'Indian Railways',
                'travel_id': 'IR202',
                'source': 'Delhi',
                'destination': 'Mumbai',
                'departure_datetime': base_datetime + timedelta(hours=4),
                'arrival_datetime': base_datetime + timedelta(hours=20),
                'base_price': Decimal('1200.00'),
                'available_seats': 30,
                'total_seats': 40
            },
            {
                'travel_type': 'BUS',
                'operator_name': 'RedBus Express',
                'travel_id': 'RB303',
                'source': 'Bangalore',
                'destination': 'Chennai',
                'departure_datetime': base_datetime + timedelta(hours=8),
                'arrival_datetime': base_datetime + timedelta(hours=14),
                'base_price': Decimal('800.00'),
                'available_seats': 25,
                'total_seats': 35
            },
            {
                'travel_type': 'FLIGHT',
                'operator_name': 'JetStream Airways',
                'travel_id': 'JS404',
                'source': 'Chennai',
                'destination': 'Kolkata',
                'departure_datetime': base_datetime + timedelta(days=1),
                'arrival_datetime': base_datetime + timedelta(days=1, hours=2, minutes=30),
                'base_price': Decimal('3800.00'),
                'available_seats': 20,
                'total_seats': 25
            },
            {
                'travel_type': 'TRAIN',
                'operator_name': 'Shatabdi Express',
                'travel_id': 'SE505',
                'source': 'Kolkata',
                'destination': 'Bangalore',
                'departure_datetime': base_datetime + timedelta(days=2),
                'arrival_datetime': base_datetime + timedelta(days=3, hours=6),
                'base_price': Decimal('2200.00'),
                'available_seats': 35,
                'total_seats': 45
            }
        ]

        for travel_data in sample_travels:
            if not TravelOption.objects.filter(travel_id=travel_data['travel_id']).exists():
                travel = TravelOption.objects.create(**travel_data)
                self.stdout.write(
                    f'   ✈️  Created travel: {travel.operator_name} ({travel.travel_id})'
                )

        # Create a sample booking
        sample_user = User.objects.filter(username='john_doe').first()
        sample_travel = TravelOption.objects.first()
        
        if sample_user and sample_travel:
            if not Booking.objects.filter(user=sample_user).exists():
                booking = Booking.objects.create(
                    user=sample_user,
                    travel_option=sample_travel,
                    number_of_seats=2,
                    contact_email=sample_user.email,
                    contact_phone=sample_user.phone_number,
                    special_requests='Window seat preferred',
                    total_amount=sample_travel.base_price * 2
                )
                self.stdout.write(f'   📋 Created sample booking: {booking.booking_id}')

        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully'))
        self.stdout.write('\n📋 Sample Login Credentials:')
        self.stdout.write('   Admin: admin / admin123')
        self.stdout.write('   User: john_doe / password123')
        self.stdout.write('   User: jane_smith / password123')