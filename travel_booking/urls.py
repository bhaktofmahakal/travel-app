"""
URL configuration for travel_booking project.
Main URL configuration with app-specific URL includes
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    
    # Home page
    path('', views.HomeView.as_view(), name='home'),
    
    # App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('travel/', include('travel.urls', namespace='travel')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    
    # API URLs (future enhancement)
    # path('api/', include('api.urls', namespace='api')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('help/', TemplateView.as_view(template_name='pages/help.html'), name='help'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error pages
handler404 = 'travel_booking.views.custom_404'
handler500 = 'travel_booking.views.custom_500'