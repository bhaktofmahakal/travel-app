/**
 * Travel Booking Platform - Main JavaScript
 * Professional frontend functionality with modern ES6+ features
 */

// Global application object
const TravelBooking = {
    init() {
        this.bindEvents();
        this.initializeComponents();
        this.setupAjaxDefaults();
    },

    bindEvents() {
        // Back to top button
        this.handleBackToTop();
        
        // Form enhancements
        this.enhanceForms();
        
        // Search functionality
        this.initSearchFeatures();
        
        // Booking functionality
        this.initBookingFeatures();
        
        // Real-time updates
        this.initRealTimeUpdates();
    },

    initializeComponents() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });

        // Initialize date pickers with restrictions
        this.initDatePickers();
        
        // Initialize autocomplete features
        this.initAutocomplete();
    },

    setupAjaxDefaults() {
        // Setup CSRF token for AJAX requests
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    }
                }
            });
        }
    },

    // Back to top functionality
    handleBackToTop() {
        const backToTop = $('#backToTop');
        
        $(window).scroll(function() {
            if ($(window).scrollTop() > 300) {
                backToTop.fadeIn();
            } else {
                backToTop.fadeOut();
            }
        });
        
        backToTop.click(function(e) {
            e.preventDefault();
            $('html, body').animate({scrollTop: 0}, 600);
        });
    },

    // Form enhancements
    enhanceForms() {
        // Add loading states to form submissions
        $('form').on('submit', function() {
            const submitBtn = $(this).find('button[type="submit"]');
            const originalText = submitBtn.text();
            
            submitBtn.prop('disabled', true)
                     .html('<span class="loading-spinner me-2"></span>' + 'Processing...');
            
            // Re-enable after 30 seconds as fallback
            setTimeout(() => {
                submitBtn.prop('disabled', false).text(originalText);
            }, 30000);
        });

        // Real-time form validation
        $('.form-control, .form-select').on('blur', function() {
            this.validateField($(this));
        });

        // Password strength indicator
        $('input[type="password"]').on('input', function() {
            this.checkPasswordStrength($(this));
        });
    },

    validateField(field) {
        const value = field.val().trim();
        const fieldName = field.attr('name');
        let isValid = true;
        let message = '';

        // Email validation
        if (fieldName === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }

        // Phone validation
        if (fieldName === 'phone_number' && value) {
            const phoneRegex = /^[+]?[\d\s\-\(\)]{10,}$/;
            if (!phoneRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid phone number';
            }
        }

        this.showFieldValidation(field, isValid, message);
    },

    showFieldValidation(field, isValid, message) {
        field.removeClass('is-valid is-invalid');
        field.siblings('.invalid-feedback, .valid-feedback').remove();
        
        if (isValid) {
            field.addClass('is-valid');
        } else {
            field.addClass('is-invalid');
            if (message) {
                field.after(`<div class="invalid-feedback">${message}</div>`);
            }
        }
    },

    checkPasswordStrength(field) {
        const password = field.val();
        let strength = 0;
        let message = '';
        let color = '';

        // Length check
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;

        // Character variety
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;

        // Determine strength level
        if (strength < 3) {
            message = 'Weak';
            color = 'danger';
        } else if (strength < 5) {
            message = 'Medium';
            color = 'warning';
        } else {
            message = 'Strong';
            color = 'success';
        }

        // Show strength indicator
        let indicator = field.siblings('.password-strength');
        if (indicator.length === 0) {
            indicator = $(`<div class="password-strength mt-1"></div>`);
            field.after(indicator);
        }

        indicator.html(`
            <div class="progress" style="height: 5px;">
                <div class="progress-bar bg-${color}" style="width: ${(strength/6)*100}%"></div>
            </div>
            <small class="text-${color}">Password strength: ${message}</small>
        `);
    },

    // Date picker initialization
    initDatePickers() {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        $('input[type="date"]').attr('min', today);

        // Departure/Return date logic
        $('#id_departure_date').on('change', function() {
            const departureDate = $(this).val();
            $('#id_return_date').attr('min', departureDate);
        });
    },

    // Autocomplete functionality
    initAutocomplete() {
        // City autocomplete for source and destination
        this.setupCityAutocomplete('#id_source');
        this.setupCityAutocomplete('#id_destination');
        
        // Popular routes suggestions
        this.loadPopularRoutes();
    },

    setupCityAutocomplete(selector) {
        $(selector).on('input', debounce(function() {
            const query = $(this).val();
            if (query.length < 2) return;

            $.ajax({
                url: '/travel/ajax/cities/',
                data: { q: query },
                success: function(data) {
                    // Update datalist
                    const datalist = $(selector).attr('list');
                    $(`#${datalist}`).empty();
                    
                    data.cities.forEach(city => {
                        $(`#${datalist}`).append(`<option value="${city}">`);
                    });
                }
            });
        }, 300));
    },

    loadPopularRoutes() {
        $.ajax({
            url: '/travel/ajax/popular-routes/',
            success: function(data) {
                const container = $('.popular-routes-suggestions');
                if (container.length) {
                    let html = '<h6>Popular Routes:</h6>';
                    data.routes.forEach(route => {
                        html += `
                            <a href="#" class="badge bg-light text-dark me-2 mb-2 route-suggestion" 
                               data-source="${route.source}" data-destination="${route.destination}">
                                ${route.source} → ${route.destination}
                            </a>
                        `;
                    });
                    container.html(html);
                }
            }
        });

        // Handle route suggestion clicks
        $(document).on('click', '.route-suggestion', function(e) {
            e.preventDefault();
            const source = $(this).data('source');
            const destination = $(this).data('destination');
            
            $('#id_source').val(source);
            $('#id_destination').val(destination);
        });
    },

    // Search functionality
    initSearchFeatures() {
        // Advanced search toggle
        $('.advanced-search-toggle').on('click', function(e) {
            e.preventDefault();
            $('.advanced-search-options').slideToggle();
            $(this).find('i').toggleClass('fa-chevron-down fa-chevron-up');
        });

        // Search form enhancements
        $('.travel-search-form').on('submit', function() {
            // Add loading state to search results
            $('.search-results').html(`
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Searching...</span>
                    </div>
                    <p class="mt-3">Finding the best travel options for you...</p>
                </div>
            `);
        });

        // Filter updates
        $('.search-filters input, .search-filters select').on('change', function() {
            this.updateSearchResults();
        });
    },

    updateSearchResults() {
        const form = $('.travel-search-form');
        const formData = form.serialize();
        
        $.ajax({
            url: form.attr('action') || '/travel/search/',
            data: formData,
            success: function(response) {
                $('.search-results').html(response);
                // Update URL without page reload
                const newUrl = `${window.location.pathname}?${formData}`;
                history.pushState(null, null, newUrl);
            },
            error: function() {
                $('.search-results').html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading search results. Please try again.
                    </div>
                `);
            }
        });
    },

    // Booking functionality
    initBookingFeatures() {
        // Passenger count updates
        $('#id_number_of_seats').on('change', function() {
            this.updatePassengerForms($(this).val());
            this.updatePriceCalculation();
        });

        // Booking confirmation
        $('.booking-form').on('submit', function(e) {
            e.preventDefault();
            this.showBookingConfirmation($(this));
        });

        // Seat selection (if applicable)
        this.initSeatSelection();
        
        // Payment integration
        this.initPaymentProcessing();
    },

    updatePassengerForms(seatCount) {
        const container = $('.passenger-forms-container');
        if (container.length === 0) return;

        // Clear existing forms
        container.empty();

        // Add forms for each passenger
        for (let i = 0; i < seatCount; i++) {
            this.addPassengerForm(container, i + 1);
        }
    },

    addPassengerForm(container, passengerNumber) {
        const formHtml = `
            <div class="passenger-form mb-4">
                <h6 class="mb-3">
                    <i class="fas fa-user me-2"></i>Passenger ${passengerNumber}
                </h6>
                <div class="row g-3">
                    <div class="col-md-2">
                        <select class="form-select" name="passenger_${passengerNumber}_title" required>
                            <option value="">Title</option>
                            <option value="Mr">Mr</option>
                            <option value="Mrs">Mrs</option>
                            <option value="Ms">Ms</option>
                            <option value="Dr">Dr</option>
                        </select>
                    </div>
                    <div class="col-md-5">
                        <input type="text" class="form-control" name="passenger_${passengerNumber}_first_name" 
                               placeholder="First Name" required>
                    </div>
                    <div class="col-md-5">
                        <input type="text" class="form-control" name="passenger_${passengerNumber}_last_name" 
                               placeholder="Last Name" required>
                    </div>
                    <div class="col-md-4">
                        <input type="date" class="form-control" name="passenger_${passengerNumber}_dob" 
                               placeholder="Date of Birth" required>
                    </div>
                    <div class="col-md-4">
                        <select class="form-select" name="passenger_${passengerNumber}_gender" required>
                            <option value="">Gender</option>
                            <option value="M">Male</option>
                            <option value="F">Female</option>
                            <option value="O">Other</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="passenger_${passengerNumber}_id_number" 
                               placeholder="ID Number" required>
                    </div>
                </div>
            </div>
        `;
        container.append(formHtml);
    },

    updatePriceCalculation() {
        const seats = parseInt($('#id_number_of_seats').val()) || 1;
        const basePrice = parseFloat($('.base-price').data('price')) || 0;
        const totalPrice = seats * basePrice;
        
        $('.total-price').text(`₹${totalPrice.toLocaleString()}`);
        
        // Update price breakdown
        $('.price-breakdown').html(`
            <div class="d-flex justify-content-between">
                <span>Base Price × ${seats}</span>
                <span>₹${(basePrice * seats).toLocaleString()}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Taxes & Fees</span>
                <span>₹${(totalPrice * 0.18).toLocaleString()}</span>
            </div>
            <hr>
            <div class="d-flex justify-content-between fw-bold">
                <span>Total Amount</span>
                <span>₹${(totalPrice * 1.18).toLocaleString()}</span>
            </div>
        `);
    },

    showBookingConfirmation(form) {
        // Create confirmation modal
        const modalHtml = `
            <div class="modal fade" id="bookingConfirmModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-check-circle me-2"></i>Confirm Booking
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="booking-summary">
                                <!-- Booking details will be populated here -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary confirm-booking-btn">
                                <i class="fas fa-credit-card me-2"></i>Proceed to Payment
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        
        // Populate booking summary
        this.populateBookingSummary(form);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('bookingConfirmModal'));
        modal.show();
        
        // Handle confirmation
        $('.confirm-booking-btn').on('click', function() {
            modal.hide();
            form[0].submit();
        });
        
        // Clean up modal after hide
        $('#bookingConfirmModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    },

    populateBookingSummary(form) {
        // Extract form data and create summary
        const formData = new FormData(form[0]);
        const summary = $('.booking-summary');
        
        // This would be populated with actual booking details
        summary.html(`
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Please review your booking details before proceeding to payment.
            </div>
            <!-- Detailed booking summary would go here -->
        `);
    },

    initSeatSelection() {
        // Seat map functionality (if implemented)
        $('.seat').on('click', function() {
            if ($(this).hasClass('occupied')) return;
            
            $(this).toggleClass('selected');
            this.updateSelectedSeats();
        });
    },

    updateSelectedSeats() {
        const selectedSeats = $('.seat.selected').map(function() {
            return $(this).data('seat-number');
        }).get();
        
        $('#selected_seats').val(selectedSeats.join(','));
        $('.selected-seats-display').text(selectedSeats.join(', ') || 'None selected');
    },

    initPaymentProcessing() {
        // Payment gateway integration would go here
        $('.payment-method').on('change', function() {
            const method = $(this).val();
            $('.payment-details').hide();
            $(`.payment-details-${method}`).show();
        });
    },

    // Real-time updates
    initRealTimeUpdates() {
        // Booking status updates
        if ($('.booking-status').length) {
            this.startBookingStatusPolling();
        }
        
        // Live seat availability
        if ($('.seat-availability').length) {
            this.startSeatAvailabilityPolling();
        }
    },

    startBookingStatusPolling() {
        const bookingId = $('.booking-status').data('booking-id');
        if (!bookingId) return;
        
        setInterval(() => {
            $.ajax({
                url: `/bookings/ajax/booking-status/${bookingId}/`,
                success: (data) => {
                    if (data.status !== $('.booking-status').data('current-status')) {
                        $('.booking-status').replaceWith(data.html);
                        this.showNotification('Booking status updated', 'info');
                    }
                }
            });
        }, 30000); // Check every 30 seconds
    },

    startSeatAvailabilityPolling() {
        const travelOptionId = $('.seat-availability').data('travel-option-id');
        if (!travelOptionId) return;
        
        setInterval(() => {
            $.ajax({
                url: `/travel/ajax/seat-availability/${travelOptionId}/`,
                success: (data) => {
                    $('.available-seats-count').text(data.available_seats);
                    if (data.available_seats < 5) {
                        $('.low-availability-warning').show();
                    }
                }
            });
        }, 60000); // Check every minute
    },

    // Utility functions
    showNotification(message, type = 'info') {
        const notification = $(`
            <div class="alert alert-${type} alert-dismissible fade show notification-alert" 
                 style="position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px;">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('body').append(notification);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            notification.alert('close');
        }, 5000);
    },

    formatCurrency(amount, currency = 'INR') {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    formatDate(date, options = {}) {
        return new Intl.DateTimeFormat('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            ...options
        }).format(new Date(date));
    }
};

// Utility function for debouncing
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Form clearing function
function clearForm() {
    const form = document.querySelector('.travel-search-form');
    if (form) {
        form.reset();
        // Reset date minimums
        const today = new Date().toISOString().split('T')[0];
        form.querySelector('#id_departure_date')?.setAttribute('min', today);
        form.querySelector('#id_return_date')?.removeAttribute('min');
    }
}

// Initialize when DOM is ready
$(document).ready(function() {
    TravelBooking.init();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause polling
        clearInterval(window.bookingStatusInterval);
        clearInterval(window.seatAvailabilityInterval);
    } else {
        // Page is visible, resume polling
        TravelBooking.initRealTimeUpdates();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TravelBooking;
}