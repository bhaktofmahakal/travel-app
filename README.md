# Travel Booking Application

A comprehensive travel booking web application built with Django that allows users to search, book, and manage travel options including flights, trains, and buses.

## 🚀 Features

### Backend Features
- **User Management**: Registration, login, logout with Django's built-in authentication
- **Travel Options**: Comprehensive model with flight, train, bus options
- **Booking System**: Complete booking workflow with passenger details
- **Booking Management**: View, filter, and cancel bookings
- **Advanced Search**: Multi-criteria search with filters

### Frontend Features
- **Responsive Design**: Bootstrap 5 responsive layout
- **User Dashboard**: Personalized dashboard with booking statistics
- **Professional UI**: Modern design with animations and interactive elements
- **Forms & Validation**: Crispy forms with comprehensive validation
- **Mobile-Friendly**: Optimized for all device types

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7, Python 3.x
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: SQLite (development), MySQL ready
- **Forms**: Django Crispy Forms
- **Authentication**: Django built-in auth system

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-booking-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Load sample data (optional)**
   ```bash
   python manage.py loaddata fixtures/sample_data.json
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Application: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

## 🗄️ Database Configuration

The application supports **multiple database backends** with easy switching via environment variables:

### 🚀 Quick Database Setup
```bash
# One command to setup everything (migrations + superuser + sample data)
python manage.py setup_database
```

### SQLite (Default - Development)
- No additional setup required
- Perfect for development and testing
- Database file: `db.sqlite3`

### MySQL Configuration
Since you have **MySQL Workbench**, you can use MySQL:

1. **Install MySQL driver:**
```bash
pip install mysqlclient
```

2. **Create database in MySQL Workbench:**
```sql
CREATE DATABASE travel_booking;
CREATE USER 'travel_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON travel_booking.* TO 'travel_user'@'localhost';
FLUSH PRIVILEGES;
```

3. **Update .env file:**
```env
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=travel_booking
DATABASE_USER=travel_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

### PostgreSQL Configuration  
Since you have **pgAdmin**, you can use PostgreSQL:

1. **Install PostgreSQL driver:**
```bash
pip install psycopg2-binary
```

2. **Create database in pgAdmin:**
```sql
CREATE DATABASE travel_booking;
CREATE USER travel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE travel_booking TO travel_user;
```

3. **Update .env file:**
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=travel_booking
DATABASE_USER=travel_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
    }
}
```

Install MySQL client:
```bash
pip install mysqlclient
```

## 📱 Usage

### For Users
1. **Register/Login**: Create account or login with existing credentials
2. **Search Travel**: Use search form to find travel options
3. **Book Travel**: Select option and complete booking process
4. **Manage Bookings**: View dashboard to manage your bookings
5. **Cancel Bookings**: Cancel bookings with refund calculation

### For Administrators
1. Access admin panel at `/admin/`
2. Manage travel options, users, and bookings
3. View booking statistics and reports

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test travel
python manage.py test bookings

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📁 Project Structure

```
travel-booking-app/
├── accounts/                # User management app
│   ├── models.py           # Custom user model
│   ├── views.py            # Auth views
│   ├── forms.py            # Registration/profile forms
│   └── templates/          # Auth templates
├── travel/                 # Travel options app
│   ├── models.py           # Travel option models
│   ├── views.py            # Search and listing views
│   ├── forms.py            # Search forms
│   └── templates/          # Travel templates
├── bookings/               # Booking management app
│   ├── models.py           # Booking models
│   ├── views.py            # Booking views
│   ├── forms.py            # Booking forms
│   └── templates/          # Booking templates
├── templates/              # Global templates
│   ├── base.html           # Base template
│   └── home.html           # Homepage
├── static/                 # Static files
├── media/                  # Media files
├── travel_booking/         # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # URL configuration
│   └── views.py            # Main views
├── requirements.txt        # Python dependencies
└── manage.py               # Django management script
```

## 🔧 Configuration

### Environment Variables
Create `.env` file for sensitive configurations:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Settings Configuration
- **Development**: Uses SQLite, DEBUG=True
- **Production**: Configure for MySQL, DEBUG=False
- **Email**: SMTP configuration for booking confirmations

## 🚀 Deployment

### PythonAnywhere Deployment
1. Upload files to PythonAnywhere
2. Create virtual environment
3. Install dependencies
4. Configure WSGI file
5. Set up MySQL database
6. Run migrations
7. Configure static files

### AWS Deployment
1. Set up EC2 instance
2. Install required software
3. Clone repository
4. Configure environment
5. Set up RDS database
6. Configure nginx/apache
7. Set up SSL certificate

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@travelbooking.com or create an issue in the repository.

## 🏆 Assignment Compliance

This application fully satisfies all assignment requirements:

### ✅ Backend Requirements
- User management with Django auth
- Travel options model with all required fields
- Booking system with complete workflow
- View and manage bookings functionality

### ✅ Frontend Requirements
- User-friendly Django templates
- Responsive design with Bootstrap
- Complete user interface for all features

### ✅ Bonus Features Implemented
- Input validation across all forms
- Advanced search and filtering
- Professional UI/UX design
- Django best practices followed

---

**Developed with ❤️ for the Travel Booking Assignment**