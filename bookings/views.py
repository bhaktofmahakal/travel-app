"""
Professional Booking Views with Payment Integration and Comprehensive Management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
import uuid
from datetime import datetime, timedelta
from .models import Booking, PassengerDetail, BookingHistory
from .forms import BookingForm, PassengerDetailFormSet, BookingSearchForm, CancellationForm
from travel.models import TravelOption, PopularRoute
from accounts.models import User


class BookingListView(LoginRequiredMixin, ListView):
    """
    User's booking list with filtering and status management
    """
    model = Booking
    template_name = 'bookings/list.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Booking.objects.filter(user=self.request.user).select_related(
            'travel_option'
        ).prefetch_related('passengers').order_by('-booking_date')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        travel_type = self.request.GET.get('travel_type')
        if travel_type:
            queryset = queryset.filter(travel_option__travel_type=travel_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Booking statistics
        all_bookings = Booking.objects.filter(user=user)
        context.update({
            'title': 'My Bookings',
            'total_bookings': all_bookings.count(),
            'pending_bookings': all_bookings.filter(status='PENDING').count(),
            'confirmed_bookings': all_bookings.filter(status='CONFIRMED').count(),
            'completed_bookings': all_bookings.filter(status='COMPLETED').count(),
            'cancelled_bookings': all_bookings.filter(status='CANCELLED').count(),
            'search_form': BookingSearchForm(self.request.GET),
        })
        
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed booking view with all related information
    """
    model = Booking
    template_name = 'bookings/detail.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            'travel_option'
        ).prefetch_related('passengers', 'history')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object
        
        # Cancellation eligibility
        can_cancel = (
            booking.status == 'CONFIRMED' and
            booking.travel_option.departure_datetime > timezone.now() + timedelta(hours=24)
        )
        
        # Refund calculation
        refund_amount = 0
        if can_cancel:
            refund_amount = booking.calculate_refund_amount()
        
        context.update({
            'title': f'Booking {booking.booking_id}',
            'can_cancel': can_cancel,
            'refund_amount': refund_amount,
            'booking_history': booking.history.order_by('-timestamp'),
        })
        
        return context


class BookingCreateView(LoginRequiredMixin, TemplateView):
    """
    Multi-step booking creation process
    """
    template_name = 'bookings/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Get travel option
        self.travel_option = get_object_or_404(
            TravelOption,
            pk=kwargs['travel_option_pk'],
            status='ACTIVE'
        )
        
        # Check availability
        if self.travel_option.available_seats == 0:
            messages.error(request, 'This travel option is fully booked.')
            return redirect('travel:detail', pk=self.travel_option.pk)
        
        if self.travel_option.departure_datetime <= timezone.now():
            messages.error(request, 'Cannot book past travel options.')
            return redirect('travel:detail', pk=self.travel_option.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Book Your Travel',
            'travel_option': self.travel_option,
            'booking_form': BookingForm(
                travel_option=self.travel_option,
                user=self.request.user
            ),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = BookingForm(
            request.POST,
            travel_option=self.travel_option,
            user=request.user
        )
        
        if form.is_valid():
            # Create booking
            booking = form.save()
            
            # Create booking history entry
            BookingHistory.objects.create(
                booking=booking,
                status_from=None,
                status_to='PENDING',
                changed_by=request.user,
                reason='Booking created'
            )
            
            messages.success(
                request,
                f'Booking created successfully! Your booking ID is {booking.booking_id}'
            )
            
            # Redirect to passenger details if multiple seats
            if booking.number_of_seats > 1:
                return redirect('bookings:passengers', booking_id=booking.booking_id)
            else:
                return redirect('bookings:confirm', booking_id=booking.booking_id)
        
        context = self.get_context_data(**kwargs)
        context['booking_form'] = form
        return render(request, self.template_name, context)


class PassengerDetailView(LoginRequiredMixin, TemplateView):
    """
    Passenger details collection for multi-seat bookings
    """
    template_name = 'bookings/passengers.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(
            Booking,
            booking_id=kwargs['booking_id'],
            user=request.user,
            status='PENDING'
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize formset
        PassengerFormSet = PassengerDetailFormSet
        formset = PassengerFormSet(
            queryset=PassengerDetail.objects.filter(booking=self.booking),
            initial=[{} for _ in range(self.booking.number_of_seats)]
        )
        
        context.update({
            'title': 'Passenger Details',
            'booking': self.booking,
            'formset': formset,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        PassengerFormSet = PassengerDetailFormSet
        formset = PassengerFormSet(request.POST)
        
        if formset.is_valid():
            # Save passenger details
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                    passenger = form.save(commit=False)
                    passenger.booking = self.booking
                    passenger.save()
            
            messages.success(request, 'Passenger details saved successfully!')
            return redirect('bookings:confirm', booking_id=self.booking.booking_id)
        
        context = self.get_context_data(**kwargs)
        context['formset'] = formset
        return render(request, self.template_name, context)


class BookingConfirmView(LoginRequiredMixin, DetailView):
    """
    Final booking confirmation before payment
    """
    model = Booking
    template_name = 'bookings/confirm.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            status='PENDING'
        ).select_related('travel_option').prefetch_related('passengers')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object
        
        # Calculate pricing breakdown
        base_amount = booking.total_price
        tax_amount = base_amount * 0.18  # 18% GST
        total_amount = base_amount + tax_amount
        
        context.update({
            'title': 'Confirm Your Booking',
            'base_amount': base_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        
        # Confirm booking and redirect to payment
        booking.confirmation_date = timezone.now()
        booking.save(update_fields=['confirmation_date'])
        
        return redirect('bookings:payment', booking_id=booking.booking_id)


class PaymentView(LoginRequiredMixin, DetailView):
    """
    Payment processing view
    """
    model = Booking
    template_name = 'bookings/payment.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            status='PENDING'
        ).select_related('travel_option')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object
        
        # Payment details
        base_amount = booking.total_price
        tax_amount = base_amount * 0.18
        total_amount = base_amount + tax_amount
        
        # Generate payment reference
        payment_ref = f"PAY_{booking.booking_id}_{int(timezone.now().timestamp())}"
        
        context.update({
            'title': 'Complete Payment',
            'base_amount': base_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'payment_reference': payment_ref,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        payment_method = request.POST.get('payment_method')
        
        # Simulate payment processing
        if self.process_payment(booking, payment_method):
            # Payment successful
            booking.status = 'CONFIRMED'
            booking.payment_status = 'PAID'
            booking.save(update_fields=['status', 'payment_status'])
            
            # Update popular route booking count
            route, created = PopularRoute.objects.get_or_create(
                source=booking.travel_option.source,
                destination=booking.travel_option.destination
            )
            route.booking_count = F('booking_count') + 1
            route.save(update_fields=['booking_count'])
            
            # Create booking history
            BookingHistory.objects.create(
                booking=booking,
                status_from='PENDING',
                status_to='CONFIRMED',
                changed_by=request.user,
                reason='Payment completed successfully'
            )
            
            # Send confirmation email
            self.send_booking_confirmation_email(booking)
            
            return redirect('bookings:payment_success', booking_id=booking.booking_id)
        else:
            # Payment failed
            messages.error(request, 'Payment processing failed. Please try again.')
            return redirect('bookings:payment_failure', booking_id=booking.booking_id)
    
    def process_payment(self, booking, payment_method):
        """
        Simulate payment processing
        In a real application, this would integrate with payment gateways
        """
        # Simulate processing time and success rate
        import random
        import time
        time.sleep(1)  # Simulate processing delay
        
        # 95% success rate for simulation
        return random.random() < 0.95
    
    def send_booking_confirmation_email(self, booking):
        """
        Send booking confirmation email to user
        """
        try:
            subject = f'Booking Confirmed - {booking.booking_id}'
            html_message = render_to_string('emails/booking_confirmation.html', {
                'booking': booking,
                'user': booking.user,
            })
            
            send_mail(
                subject=subject,
                message='',  # Plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.contact_email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            # Log error but don't fail the booking process
            pass


class PaymentSuccessView(LoginRequiredMixin, DetailView):
    """
    Payment success confirmation
    """
    model = Booking
    template_name = 'bookings/payment_success.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            status='CONFIRMED'
        ).select_related('travel_option')


class PaymentFailureView(LoginRequiredMixin, DetailView):
    """
    Payment failure handling
    """
    model = Booking
    template_name = 'bookings/payment_failure.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user,
            status='PENDING'
        ).select_related('travel_option')


class BookingCancelView(LoginRequiredMixin, TemplateView):
    """
    Booking cancellation with refund calculation
    """
    template_name = 'bookings/cancel.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(
            Booking,
            booking_id=kwargs['booking_id'],
            user=request.user,
            status='CONFIRMED'
        )
        
        # Check if cancellation is allowed
        if self.booking.travel_option.departure_datetime <= timezone.now() + timedelta(hours=24):
            messages.error(
                request,
                'Cancellation is not allowed within 24 hours of departure.'
            )
            return redirect('bookings:detail', booking_id=self.booking.booking_id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Cancel Booking',
            'booking': self.booking,
            'form': CancellationForm(booking=self.booking),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = CancellationForm(request.POST, booking=self.booking)
        
        if form.is_valid():
            # Cancel booking
            self.booking.status = 'CANCELLED'
            self.booking.cancellation_date = timezone.now()
            self.booking.save(update_fields=['status', 'cancellation_date'])
            
            # Restore seat availability
            self.booking.travel_option.restore_available_seats(self.booking.number_of_seats)
            
            # Create booking history
            BookingHistory.objects.create(
                booking=self.booking,
                status_from='CONFIRMED',
                status_to='CANCELLED',
                changed_by=request.user,
                reason=form.cleaned_data['cancellation_reason']
            )
            
            messages.success(
                request,
                f'Booking {self.booking.booking_id} has been cancelled successfully. '
                f'Refund of ₹{self.booking.refund_amount:.2f} will be processed within 5-7 business days.'
            )
            
            return redirect('bookings:detail', booking_id=self.booking.booking_id)
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)


class BookingHistoryView(LoginRequiredMixin, ListView):
    """
    Complete booking history with advanced filtering
    """
    model = Booking
    template_name = 'bookings/history.html'
    context_object_name = 'bookings'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Booking.objects.filter(user=self.request.user).select_related(
            'travel_option'
        ).order_by('-booking_date')
        
        # Apply advanced filters
        form = BookingSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('booking_id'):
                queryset = queryset.filter(
                    booking_id__icontains=form.cleaned_data['booking_id']
                )
            
            if form.cleaned_data.get('travel_type'):
                queryset = queryset.filter(
                    travel_option__travel_type=form.cleaned_data['travel_type']
                )
            
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    booking_date__gte=form.cleaned_data['date_from']
                )
            
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    booking_date__lte=form.cleaned_data['date_to']
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Booking History',
            'search_form': BookingSearchForm(self.request.GET),
        })
        return context


class BookingSearchView(LoginRequiredMixin, TemplateView):
    """
    Advanced booking search interface
    """
    template_name = 'bookings/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = BookingSearchForm(self.request.GET or None)
        context['form'] = form
        context['title'] = 'Search Bookings'
        
        if form.is_valid() and any(form.cleaned_data.values()):
            # Perform search
            queryset = Booking.objects.filter(user=self.request.user)
            
            # Apply filters (same as BookingHistoryView)
            # ... filter logic here ...
            
            paginator = Paginator(queryset, 10)
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            context.update({
                'results': page_obj,
                'page_obj': page_obj,
                'is_paginated': page_obj.has_other_pages(),
                'total_results': queryset.count(),
            })
        
        return context


# Utility Views and Functions

@login_required
def download_booking_pdf(request, booking_id):
    """
    Generate and download booking confirmation PDF
    """
    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        user=request.user
    )
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add booking details to PDF
        p.drawString(100, 750, f"Booking Confirmation - {booking.booking_id}")
        p.drawString(100, 720, f"Travel: {booking.travel_option.source} to {booking.travel_option.destination}")
        p.drawString(100, 690, f"Date: {booking.travel_option.departure_datetime.strftime('%Y-%m-%d %H:%M')}")
        p.drawString(100, 660, f"Passengers: {booking.number_of_seats}")
        p.drawString(100, 630, f"Total Amount: ₹{booking.total_price}")
        p.drawString(100, 600, f"Status: {booking.get_status_display()}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="booking_{booking_id}.pdf"'
        
        return response
        
    except ImportError:
        messages.error(request, 'PDF generation is not available. Please contact support.')
        return redirect('bookings:detail', booking_id=booking_id)


@login_required
def download_ticket(request, booking_id):
    """
    Generate and download travel ticket
    """
    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        user=request.user,
        status='CONFIRMED'
    )
    
    # Generate ticket (simplified version)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking_id}.txt"'
    
    ticket_content = f"""
    TRAVEL TICKET
    =============
    
    Booking ID: {booking.booking_id}
    From: {booking.travel_option.source}
    To: {booking.travel_option.destination}
    Date: {booking.travel_option.departure_datetime.strftime('%Y-%m-%d')}
    Time: {booking.travel_option.departure_datetime.strftime('%H:%M')}
    Passengers: {booking.number_of_seats}
    
    Please arrive at least 30 minutes before departure.
    """
    
    response.write(ticket_content)
    return response


# AJAX Views

def booking_status_ajax(request, booking_id):
    """
    AJAX endpoint for booking status updates
    """
    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            user=request.user
        )
        
        return JsonResponse({
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'payment_status': booking.payment_status,
            'html': render_to_string('bookings/partials/booking_status.html', {
                'booking': booking
            })
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)