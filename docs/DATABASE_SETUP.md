# Database Setup Guide

The Travel Booking application supports multiple database backends. Choose the one that suits your needs.

## 🗄️ Supported Databases

### 1. **SQLite (Default - No Setup Required)**
- **Best for**: Development and testing
- **Pros**: Zero configuration, file-based, included with Python
- **Cons**: Not suitable for production with multiple users

```env
DATABASE_ENGINE=django.db.backends.sqlite3
```

### 2. **MySQL Setup** 

#### Prerequisites:
- MySQL Server installed
- MySQL Workbench (you already have this!)

#### Steps:

1. **Install MySQL Driver:**
```bash
pip install mysqlclient
```

2. **Create Database in MySQL Workbench:**
```sql
CREATE DATABASE travel_booking;
CREATE USER 'travel_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON travel_booking.* TO 'travel_user'@'localhost';
FLUSH PRIVILEGES;
```

3. **Update .env file:**
```env
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=travel_booking
DATABASE_USER=travel_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

### 3. **PostgreSQL Setup**

#### Prerequisites:
- PostgreSQL Server installed
- pgAdmin (you already have this!)

#### Steps:

1. **Install PostgreSQL Driver:**
```bash
pip install psycopg2-binary
```

2. **Create Database in pgAdmin:**
   - Right-click on "Databases" → Create → Database
   - Database name: `travel_booking`
   - Owner: Create a new role or use existing one

   Or use SQL:
```sql
CREATE DATABASE travel_booking;
CREATE USER travel_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE travel_booking TO travel_user;
```

3. **Update .env file:**
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=travel_booking
DATABASE_USER=travel_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

## 🚀 Migration Commands

After setting up your database:

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

## 🔧 Database Commands

### View current database configuration:
```bash
python manage.py dbshell
```

### Reset database (⚠️ **WARNING: This will delete all data**):
```bash
# For development only
python manage.py flush
python manage.py migrate
```

### Backup database:

**MySQL:**
```bash
mysqldump -u travel_user -p travel_booking > backup.sql
```

**PostgreSQL:**
```bash
pg_dump -U travel_user -h localhost travel_booking > backup.sql
```

## 🛠️ Troubleshooting

### Common MySQL Issues:

**Error: `django.db.utils.OperationalError: (1045, "Access denied for user")`**
- Check username/password in .env file
- Ensure user has proper privileges
- Verify MySQL server is running

**Error: `ModuleNotFoundError: No module named 'MySQLdb'`**
- Install mysqlclient: `pip install mysqlclient`
- On Windows, you might need Microsoft C++ Build Tools

### Common PostgreSQL Issues:

**Error: `django.db.utils.OperationalError: FATAL: database "travel_booking" does not exist`**
- Create database in pgAdmin first
- Check database name spelling in .env

**Error: `ModuleNotFoundError: No module named 'psycopg2'`**
- Install driver: `pip install psycopg2-binary`

### Performance Tips:

**For Production:**
- Use connection pooling
- Configure proper indexes
- Regular database maintenance
- Monitor query performance

**MySQL Optimization:**
```sql
-- Add to MySQL configuration
innodb_buffer_pool_size = 1G
query_cache_size = 256M
```

**PostgreSQL Optimization:**
```sql
-- Add to postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
```

## 📊 Database Schema

The application creates the following main tables:
- `auth_user_custom` - User accounts
- `travel_traveloption` - Available travel options
- `bookings_booking` - User bookings
- `bookings_passengerdetail` - Passenger information
- `accounts_userpreferences` - User preferences
- `travel_popularroute` - Popular routes tracking

## 🔄 Switching Between Databases

You can easily switch databases by:
1. Changing `DATABASE_ENGINE` in .env file
2. Running migrations: `python manage.py migrate`
3. Optionally import data from previous database

Remember to backup your data before switching!