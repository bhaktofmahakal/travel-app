"""
Main project views
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count
from travel.models import TravelOption, PopularRoute
from bookings.models import Booking
from travel.forms import QuickSearchForm


class HomeView(TemplateView):
    """
    Home page view with search form and featured content
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Quick search form
        context['search_form'] = QuickSearchForm()
        
        # Featured travel options
        context['featured_travels'] = TravelOption.objects.filter(
            is_featured=True,
            status='ACTIVE'
        ).select_related().order_by('-created_at')[:6]
        
        # Popular routes
        context['popular_routes'] = PopularRoute.objects.order_by(
            '-booking_count', '-search_count'
        )[:5]
        
        # Travel statistics
        context['stats'] = {
            'total_travels': TravelOption.objects.filter(status='ACTIVE').count(),
            'total_bookings': Booking.objects.filter(status__in=['CONFIRMED', 'COMPLETED']).count(),
            'destinations': TravelOption.objects.values('destination').distinct().count(),
            'operators': TravelOption.objects.values('operator_name').distinct().count(),
        }
        
        return context


def custom_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)