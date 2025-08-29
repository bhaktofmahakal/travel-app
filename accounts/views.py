"""
Professional Account Views with Enhanced Security and User Experience
"""

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView
from django.db.models import Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import User, UserPreferences
from .forms import CustomUserRegistrationForm, UserProfileForm, UserPreferencesForm
from bookings.models import Booking
from travel.models import TravelOption


class RegisterView(CreateView):
    """
    User registration view with enhanced validation and welcome experience
    """
    model = User
    form_class = CustomUserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Create user preferences
        UserPreferences.objects.get_or_create(user=user)
        
        # Log the user in
        login(self.request, user)
        
        messages.success(
            self.request, 
            f'Welcome {user.get_full_name() or user.username}! Your account has been created successfully.'
        )
        
        return redirect('accounts:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Your Account'
        return context


class CustomLoginView(LoginView):
    """
    Enhanced login view with better UX and security features
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Custom redirect logic
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        # Log successful login
        user = form.get_user()
        messages.success(
            self.request, 
            f'Welcome back, {user.get_full_name() or user.username}!'
        )
        
        # Update last login manually if needed
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Invalid login credentials. Please check your username and password.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sign In to Your Account'
        return context


class CustomLogoutView(LogoutView):
    """
    Custom logout view with confirmation message
    """
    next_page = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been successfully logged out.')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, DetailView):
    """
    User profile display view
    """
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Get user statistics
        bookings = Booking.objects.filter(user=user)
        context.update({
            'title': 'My Profile',
            'total_bookings': bookings.count(),
            'confirmed_bookings': bookings.filter(status='CONFIRMED').count(),
            'completed_trips': bookings.filter(status='COMPLETED').count(),
            'total_spent': bookings.filter(
                status__in=['CONFIRMED', 'COMPLETED']
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
            'recent_bookings': bookings.order_by('-booking_date')[:5],
        })
        
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    User profile editing view
    """
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Profile'
        
        # Add preferences form
        user = self.object
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        context['preferences_form'] = UserPreferencesForm(instance=preferences)
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        
        # Handle preferences form
        preferences_form = UserPreferencesForm(
            self.request.POST, 
            instance=self.object.preferences
        )
        if preferences_form.is_valid():
            preferences_form.save()
            messages.success(self.request, 'Your preferences have been updated!')
        
        return super().form_valid(form)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    Enhanced password change view
    """
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            'Your password has been changed successfully!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Change Password'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Comprehensive user dashboard with analytics and quick actions
    """
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's bookings with related data
        bookings = Booking.objects.filter(user=user).select_related(
            'travel_option'
        ).order_by('-booking_date')
        
        # Dashboard statistics
        total_bookings = bookings.count()
        confirmed_bookings = bookings.filter(status='CONFIRMED')
        completed_bookings = bookings.filter(status='COMPLETED')
        pending_bookings = bookings.filter(status='PENDING')
        
        # Financial statistics
        total_spent = bookings.filter(
            status__in=['CONFIRMED', 'COMPLETED']
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Recent activity
        recent_bookings = bookings[:5]
        
        # Upcoming trips
        upcoming_trips = confirmed_bookings.filter(
            travel_option__departure_datetime__gte=timezone.now()
        ).order_by('travel_option__departure_datetime')[:3]
        
        # Travel statistics by type
        travel_stats = bookings.filter(status__in=['CONFIRMED', 'COMPLETED']).values(
            'travel_option__travel_type'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Monthly booking trends (last 6 months)
        monthly_stats = []
        for i in range(6):
            date = timezone.now() - timezone.timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
            
            count = bookings.filter(
                booking_date__gte=month_start,
                booking_date__lte=month_end
            ).count()
            
            monthly_stats.append({
                'month': date.strftime('%B %Y'),
                'count': count
            })
        
        monthly_stats.reverse()
        
        context.update({
            'title': 'Dashboard',
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings.count(),
            'completed_bookings': completed_bookings.count(),
            'pending_bookings': pending_bookings.count(),
            'total_spent': total_spent,
            'recent_bookings': recent_bookings,
            'upcoming_trips': upcoming_trips,
            'travel_stats': travel_stats,
            'monthly_stats': monthly_stats,
        })
        
        return context


@login_required
def user_preferences_ajax(request):
    """
    AJAX endpoint for updating user preferences
    """
    if request.method == 'POST':
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        form = UserPreferencesForm(request.POST, instance=preferences)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Preferences updated successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def dashboard_stats_ajax(request):
    """
    AJAX endpoint for dashboard statistics
    """
    user = request.user
    bookings = Booking.objects.filter(user=user)
    
    stats = {
        'total_bookings': bookings.count(),
        'confirmed_bookings': bookings.filter(status='CONFIRMED').count(),
        'completed_bookings': bookings.filter(status='COMPLETED').count(),
        'pending_bookings': bookings.filter(status='PENDING').count(),
        'total_spent': float(bookings.filter(
            status__in=['CONFIRMED', 'COMPLETED']
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0),
    }
    
    return JsonResponse(stats)


class UserBookingHistoryView(LoginRequiredMixin, TemplateView):
    """
    Comprehensive booking history with filtering and pagination
    """
    template_name = 'accounts/booking_history.html'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get filter parameters
        status_filter = self.request.GET.get('status', '')
        travel_type_filter = self.request.GET.get('travel_type', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Build query
        bookings = Booking.objects.filter(user=user).select_related(
            'travel_option'
        ).order_by('-booking_date')
        
        # Apply filters
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        if travel_type_filter:
            bookings = bookings.filter(travel_option__travel_type=travel_type_filter)
        
        if date_from:
            bookings = bookings.filter(booking_date__gte=date_from)
        
        if date_to:
            bookings = bookings.filter(booking_date__lte=date_to)
        
        # Pagination
        paginator = Paginator(bookings, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'title': 'Booking History',
            'bookings': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'filter_status': status_filter,
            'filter_travel_type': travel_type_filter,
            'filter_date_from': date_from,
            'filter_date_to': date_to,
        })
        
        return context