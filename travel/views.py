"""
Professional Travel Views with Advanced Search and Analytics
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q, Count, Avg, Min, Max, F

from django.http import JsonResponse, Http404
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from django.conf import settings
import json
from datetime import datetime, timedelta
from .models import TravelOption, PopularRoute, TravelOperator
from .forms import TravelSearchForm, TravelOptionForm
from bookings.models import Booking


class TravelOptionListView(ListView):
    """
    Enhanced travel options listing with smart filtering
    """
    model = TravelOption
    template_name = 'travel/list.html'
    context_object_name = 'travels'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = TravelOption.objects.filter(
            status='ACTIVE',
            departure_datetime__gte=timezone.now()
        ).select_related().order_by('departure_datetime')
        
        # Apply basic filters
        travel_type = self.request.GET.get('travel_type')
        if travel_type:
            queryset = queryset.filter(travel_type=travel_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get travel statistics
        context.update({
            'title': 'Browse Travel Options',
            'total_options': self.get_queryset().count(),
            'travel_types': TravelOption.objects.values('travel_type').annotate(
                count=Count('id')
            ).filter(count__gt=0),
            'featured_options': TravelOption.objects.filter(
                is_featured=True,
                status='ACTIVE',
                departure_datetime__gte=timezone.now()
            ).order_by('?')[:6],
        })
        
        return context


class TravelSearchView(TemplateView):
    """
    Advanced travel search with intelligent filtering and sorting
    """
    template_name = 'travel/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = TravelSearchForm(self.request.GET or None)
        context['form'] = form
        context['title'] = 'Search Travel Options'
        
        if form.is_valid():
            # Get search results
            results = self.get_search_results(form.cleaned_data)
            
            # Pagination
            paginator = Paginator(results, 10)
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            context.update({
                'results': page_obj,
                'page_obj': page_obj,
                'is_paginated': page_obj.has_other_pages(),
                'total_results': results.count(),
                'search_performed': True,
            })
            
            # Update popular route tracking
            source = form.cleaned_data.get('source')
            destination = form.cleaned_data.get('destination')
            if source and destination:
                self.update_route_popularity(source, destination)
        
        return context
    
    def get_search_results(self, search_data):
        """
        Build optimized search query with filters
        """
        queryset = TravelOption.objects.filter(
            status='ACTIVE',
            departure_datetime__gte=timezone.now()
        ).select_related()
        
        # Required filters
        source = search_data.get('source')
        destination = search_data.get('destination')
        departure_date = search_data.get('departure_date')
        
        if source:
            queryset = queryset.filter(
                Q(source__icontains=source) | Q(source_code__icontains=source)
            )
        
        if destination:
            queryset = queryset.filter(
                Q(destination__icontains=destination) | Q(destination_code__icontains=destination)
            )
        
        if departure_date:
            queryset = queryset.filter(departure_datetime__date=departure_date)
        
        # Optional filters
        travel_type = search_data.get('travel_type')
        if travel_type:
            queryset = queryset.filter(travel_type=travel_type)
        
        min_price = search_data.get('min_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        
        max_price = search_data.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        min_seats = search_data.get('min_seats')
        if min_seats:
            queryset = queryset.filter(available_seats__gte=min_seats)
        
        # Sorting
        sort_by = search_data.get('sort_by', 'departure_datetime')
        if sort_by in ['departure_datetime', 'base_price', '-base_price', 'duration', '-available_seats']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def update_route_popularity(self, source, destination):
        """
        Update popular route statistics
        """
        route, created = PopularRoute.objects.get_or_create(
            source=source.strip().title(),
            destination=destination.strip().title()
        )
        route.search_count = F('search_count') + 1
        route.save(update_fields=['search_count'])


class TravelOptionDetailView(DetailView):
    """
    Detailed travel option view with booking integration
    """
    model = TravelOption
    template_name = 'travel/detail.html'
    context_object_name = 'travel'
    
    def get_queryset(self):
        return TravelOption.objects.filter(status='ACTIVE').select_related()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        travel = self.object
        
        # Similar options
        similar_options = TravelOption.objects.filter(
            Q(source=travel.source, destination=travel.destination) |
            Q(travel_type=travel.travel_type),
            status='ACTIVE',
            departure_datetime__gte=timezone.now()
        ).exclude(pk=travel.pk).order_by('base_price')[:5]
        
        # Check availability status
        availability_status = 'available'
        if travel.available_seats == 0:
            availability_status = 'sold_out'
        elif travel.available_seats <= 5:
            availability_status = 'limited'
        
        context.update({
            'title': f'{travel.source} to {travel.destination}',
            'similar_options': similar_options,
            'availability_status': availability_status,
            'booking_allowed': travel.available_seats > 0 and travel.departure_datetime > timezone.now(),
        })
        
        return context


class TravelOptionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create new travel option (Staff/Admin only)
    """
    model = TravelOption
    form_class = TravelOptionForm
    template_name = 'travel/create.html'
    success_url = reverse_lazy('travel:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel option created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Travel Option'
        return context


class TravelOptionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update existing travel option (Staff/Admin only)
    """
    model = TravelOption
    form_class = TravelOptionForm
    template_name = 'travel/update.html'
    success_url = reverse_lazy('travel:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel option updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Travel Option'
        return context


class TravelOptionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete travel option (Staff/Admin only)
    """
    model = TravelOption
    template_name = 'travel/delete.html'
    success_url = reverse_lazy('travel:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel option deleted successfully!')
        return super().delete(request, *args, **kwargs)


class TravelAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Comprehensive analytics dashboard for travel data
    """
    template_name = 'travel/analytics.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics
        total_options = TravelOption.objects.count()
        active_options = TravelOption.objects.filter(status='ACTIVE').count()
        featured_options = TravelOption.objects.filter(is_featured=True).count()
        
        # Travel type distribution
        travel_type_stats = TravelOption.objects.values('travel_type').annotate(
            count=Count('id'),
            avg_price=Avg('base_price'),
            total_capacity=Sum('total_seats'),
            available_seats=Sum('available_seats')
        ).order_by('-count')
        
        # Popular routes
        popular_routes = PopularRoute.objects.order_by('-booking_count', '-search_count')[:10]
        
        # Price analysis
        price_stats = TravelOption.objects.aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price'),
            avg_price=Avg('base_price')
        )
        
        # Occupancy rates by travel type
        occupancy_stats = TravelOption.objects.values('travel_type').annotate(
            total_capacity=Sum('total_seats'),
            available_seats=Sum('available_seats'),
            occupied_seats=F('total_capacity') - F('available_seats')
        ).annotate(
            occupancy_rate=F('occupied_seats') * 100.0 / F('total_capacity')
        )
        
        # Recent bookings trend
        booking_trends = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            bookings = Booking.objects.filter(
                booking_date__date=date,
                status__in=['CONFIRMED', 'COMPLETED']
            ).count()
            booking_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'bookings': bookings
            })
        booking_trends.reverse()
        
        # Operator performance
        operator_stats = TravelOperator.objects.annotate(
            option_count=Count('traveloption'),
            avg_price=Avg('traveloption__base_price')
        ).order_by('-option_count')[:10]
        
        context.update({
            'title': 'Travel Analytics Dashboard',
            'total_options': total_options,
            'active_options': active_options,
            'featured_options': featured_options,
            'travel_type_stats': travel_type_stats,
            'popular_routes': popular_routes,
            'price_stats': price_stats,
            'occupancy_stats': occupancy_stats,
            'booking_trends': booking_trends,
            'operator_stats': operator_stats,
        })
        
        return context


# AJAX Views
def popular_routes_ajax(request):
    """
    AJAX endpoint for popular routes data
    """
    routes = PopularRoute.objects.order_by('-booking_count', '-search_count')[:10]
    data = {
        'routes': [
            {
                'source': route.source,
                'destination': route.destination,
                'search_count': route.search_count,
                'booking_count': route.booking_count
            }
            for route in routes
        ]
    }
    return JsonResponse(data)


def cities_autocomplete(request):
    """
    AJAX endpoint for city autocomplete
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'cities': []})
    
    # Cache key for autocomplete results
    cache_key = f'cities_autocomplete_{query.lower()}'
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return JsonResponse(cached_result)
    
    # Get cities from source and destination fields
    sources = TravelOption.objects.filter(
        Q(source__icontains=query) | Q(source_code__icontains=query)
    ).values_list('source', flat=True).distinct()[:10]
    
    destinations = TravelOption.objects.filter(
        Q(destination__icontains=query) | Q(destination_code__icontains=query)
    ).values_list('destination', flat=True).distinct()[:10]
    
    # Combine and deduplicate
    cities = list(set(list(sources) + list(destinations)))[:15]
    cities.sort()
    
    result = {'cities': cities}
    
    # Cache for 1 hour
    cache.set(cache_key, result, 3600)
    
    return JsonResponse(result)


def seat_availability_ajax(request, travel_option_id):
    """
    AJAX endpoint for real-time seat availability
    """
    try:
        travel_option = TravelOption.objects.get(pk=travel_option_id)
        return JsonResponse({
            'available_seats': travel_option.available_seats,
            'total_seats': travel_option.total_seats,
            'occupancy_percentage': travel_option.occupancy_percentage,
            'status': travel_option.status
        })
    except TravelOption.DoesNotExist:
        return JsonResponse({'error': 'Travel option not found'}, status=404)


@login_required
def travel_comparison_ajax(request):
    """
    AJAX endpoint for comparing travel options
    """
    option_ids = request.GET.getlist('options[]')
    if not option_ids:
        return JsonResponse({'error': 'No options provided'}, status=400)
    
    options = TravelOption.objects.filter(
        pk__in=option_ids,
        status='ACTIVE'
    ).values(
        'id', 'travel_type', 'operator_name', 'source', 'destination',
        'departure_datetime', 'arrival_datetime', 'duration', 'base_price',
        'available_seats', 'amenities'
    )
    
    return JsonResponse({
        'options': list(options),
        'comparison_url': request.build_absolute_uri()
    })


def travel_filters_ajax(request):
    """
    AJAX endpoint for dynamic filter options
    """
    # Get filter data based on current search
    source = request.GET.get('source', '')
    destination = request.GET.get('destination', '')
    
    queryset = TravelOption.objects.filter(status='ACTIVE')
    
    if source:
        queryset = queryset.filter(source__icontains=source)
    if destination:
        queryset = queryset.filter(destination__icontains=destination)
    
    # Get available filter options
    operators = queryset.values_list('operator_name', flat=True).distinct()
    price_range = queryset.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )
    
    return JsonResponse({
        'operators': sorted(list(set(operators))),
        'price_range': price_range,
        'travel_types': [choice[0] for choice in TravelOption.TRAVEL_TYPES],
    })