"""
URL configuration for bookings app
"""

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking URLs
    path('', views.BookingListView.as_view(), name='list'),
    path('create/<int:travel_option_pk>/', views.BookingCreateView.as_view(), name='create'),
    path('detail/<str:booking_id>/', views.BookingDetailView.as_view(), name='detail'),
    path('cancel/<str:booking_id>/', views.BookingCancelView.as_view(), name='cancel'),
    
    # Passenger details
    path('passengers/<str:booking_id>/', views.PassengerDetailView.as_view(), name='passengers'),
    
    # Booking confirmation and payment
    path('confirm/<str:booking_id>/', views.BookingConfirmView.as_view(), name='confirm'),
    path('payment/<str:booking_id>/', views.PaymentView.as_view(), name='payment'),
    path('payment/success/<str:booking_id>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failure/<str:booking_id>/', views.PaymentFailureView.as_view(), name='payment_failure'),
    
    # Booking management
    path('history/', views.BookingHistoryView.as_view(), name='history'),
    path('search/', views.BookingSearchView.as_view(), name='search'),
    
    # Export and download
    path('download/<str:booking_id>/', views.download_booking_pdf, name='download_pdf'),
    path('download/<str:booking_id>/ticket/', views.download_ticket, name='download_ticket'),
    
    # AJAX endpoints
    path('ajax/booking-status/<str:booking_id>/', views.booking_status_ajax, name='booking_status_ajax'),
]