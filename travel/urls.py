"""
URL configuration for travel app
"""

from django.urls import path
from . import views

app_name = 'travel'

urlpatterns = [
    # Travel option URLs
    path('', views.TravelOptionListView.as_view(), name='list'),
    path('search/', views.TravelSearchView.as_view(), name='search'),
    path('detail/<int:pk>/', views.TravelOptionDetailView.as_view(), name='detail'),
    
    # AJAX endpoints
    path('ajax/popular-routes/', views.popular_routes_ajax, name='popular_routes_ajax'),
    path('ajax/cities/', views.cities_autocomplete, name='cities_autocomplete'),
    
    # Management URLs (for staff/admin)
    path('create/', views.TravelOptionCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.TravelOptionUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.TravelOptionDeleteView.as_view(), name='delete'),
    
    # Analytics and reports
    path('analytics/', views.TravelAnalyticsView.as_view(), name='analytics'),
]