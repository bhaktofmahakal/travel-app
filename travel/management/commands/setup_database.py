"""
Management command to setup database with sample data
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup database with migrations, superuser, and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation',
        )
        parser.add_argument(
            '--skip-sample-data',
            action='store_true',
            help='Skip loading sample data',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Superuser username (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Superuser email (default: admin@example.com)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up Travel Booking Database...'))
        
        # Step 1: Make migrations
        self.stdout.write('\n1️⃣ Creating migrations...')
        call_command('makemigrations', verbosity=0)
        self.stdout.write(self.style.SUCCESS('   ✅ Migrations created'))
        
        # Step 2: Apply migrations
        self.stdout.write('\n2️⃣ Applying migrations...')
        call_command('migrate', verbosity=0)
        self.stdout.write(self.style.SUCCESS('   ✅ Migrations applied'))
        
        # Step 3: Create superuser
        if not options['skip_superuser']:
            self.stdout.write('\n3️⃣ Creating superuser...')
            username = options['username']
            email = options['email']
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️ Superuser "{username}" already exists')
                )
            else:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password='admin123',
                    first_name='Super',
                    last_name='Admin'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Superuser "{username}" created')
                )
                self.stdout.write(
                    self.style.WARNING(f'   🔑 Password: admin123 (Change this in production!)')
                )
        
        # Step 4: Load sample data
        if not options['skip_sample_data']:
            self.stdout.write('\n4️⃣ Loading sample data...')
            try:
                call_command('loaddata', 'fixtures/sample_data.json', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✅ Sample data loaded'))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Failed to load sample data: {e}')
                )
        
        # Step 5: Collect static files (for production)
        self.stdout.write('\n5️⃣ Collecting static files...')
        call_command('collectstatic', '--noinput', verbosity=0)
        self.stdout.write(self.style.SUCCESS('   ✅ Static files collected'))
        
        # Final message
        self.stdout.write(self.style.SUCCESS('\n🎉 Database setup completed successfully!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run: python manage.py runserver')
        self.stdout.write('2. Visit: http://localhost:8000')
        self.stdout.write(f'3. Admin panel: http://localhost:8000/admin/')
        
        if not options['skip_superuser']:
            self.stdout.write(f'   Username: {options["username"]}')
            self.stdout.write(f'   Password: admin123')
            
        self.stdout.write('\n🗄️ Database Information:')
        from django.conf import settings
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine:
            self.stdout.write(f'   Database: SQLite (db.sqlite3)')
        elif 'mysql' in db_engine:
            self.stdout.write(f'   Database: MySQL ({settings.DATABASES["default"]["NAME"]})')
        elif 'postgresql' in db_engine:
            self.stdout.write(f'   Database: PostgreSQL ({settings.DATABASES["default"]["NAME"]})')
        else:
            self.stdout.write(f'   Database: {db_engine}')