/**
 * GiveButter Widget Tracking Integration
 * Handles events from GiveButter iframes for Google Analytics 4 and Meta Pixel
 */

// Helper to get location parameter or default context
function getLocationContext() {
    if (window.location.search) {
        const urlParams = new URLSearchParams(window.location.search);
        const loc = urlParams.get('loc');
        if (loc) return loc;
    }
    // Fallback for homepage or no param
    return window.location.pathname === '/' ? 'homepage' : 'unknown';
}

// Unified GiveButter Success Handler
function handleGiveButterSuccess(event) {
    // Normalize data from CustomEvent or MessageEvent
    let data = event.detail || event.data;
    if (data && data.givebutter) data = data.givebutter; // Handle postMessage wrapping
    
    // Check for donation vs signup
    // 1. Explicit event type check (most reliable for this widget)
    // 2. Data check (fallback)
    const isExplicitDonationEvent = data.event === 'donation.complete';
    const hasDonationAmount = data && (data.amount > 0 || data.total > 0 || data.plan_id);
    
    const isDonation = isExplicitDonationEvent || hasDonationAmount;
    
    // Get location for analytics
    const locationId = getLocationContext();

    // Use 'total' if 'amount' is missing (GiveButter sometimes uses 'total')
    const donationAmount = parseFloat(data.amount || data.total || 0);

    if (isDonation) {
        // --- DONATION TRACKING ---
        if (typeof gtag !== 'undefined') {
            console.log('✅ Tracking GA Purchase:', donationAmount);
            gtag('event', 'purchase', {
                'transaction_id': data.id || ('don_' + Date.now()),
                'value': donationAmount,
                'currency': 'USD',
                'event_category': 'Donation',
                'event_label': 'Location ' + locationId,
                'location_id': locationId
            });
        }
        
        if (typeof fbq !== 'undefined') {
            console.log('✅ Tracking FB Pixel Purchase:', donationAmount);
            fbq('track', 'Purchase', {
                value: donationAmount,
                currency: 'USD',
                content_name: 'Bike Donation',
                content_type: 'donation',
                location_id: locationId
            });
        }
        
    } else {
        // --- SIGNUP TRACKING ---
        if (typeof gtag !== 'undefined') {
            console.log('✅ Tracking GA Signup');
            gtag('event', 'email_signup', {
                'event_category': 'Conversion',
                'event_label': 'Location ' + locationId,
                'location_id': locationId
            });
        }
        
        if (typeof fbq !== 'undefined') {
            console.log('✅ Tracking FB Pixel Signup');
            fbq('track', 'Subscribe', {
                location_id: locationId
            });
        }

        // Show local Thank You UI for signups (Donate page only)
        const thankYouMessage = document.getElementById('thank-you-message');
        const donationSection = document.getElementById('donation-section');
        
        if (thankYouMessage && !thankYouMessage.classList.contains('show')) {
            thankYouMessage.classList.add('show');
            thankYouMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Nudge towards donation after a delay
            setTimeout(function() {
                if (donationSection) {
                    donationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 1200);
        }
    }
}

// Main Event Listener setup
function initGiveButterTracking() {
    console.log('GiveButter Tracking Initialized');

    // Listen for postMessage events from GiveButter iframe
    window.addEventListener('message', function(event) {
        // Check for standard success events
        if (event.data && (
            event.data.type === 'givebutter:form:success' ||
            event.data.type === 'givebutter:success' ||
            (event.data.givebutter && event.data.givebutter.success)
        )) {
            handleGiveButterSuccess(event);
        }

        // Check for intermediate donation events
        if (event.data && event.data.givebutter && event.data.event) {
            const data = event.data;
            const locationId = getLocationContext();

            if (data.event === 'donation.started') {
                if (typeof gtag !== 'undefined') {
                    console.log('✅ Tracking GA Begin Checkout');
                    gtag('event', 'begin_checkout', {
                        'currency': 'USD',
                        'value': parseFloat(data.total || 0),
                        'event_category': 'Donation',
                        'event_label': 'Location ' + locationId,
                        'location_id': locationId
                    });
                }
            } else if (data.event === 'donation.button.next') {
                if (typeof gtag !== 'undefined') {
                    console.log('✅ Tracking GA Checkout Progress');
                    gtag('event', 'checkout_progress', {
                        'currency': 'USD',
                        'value': parseFloat(data.total || 0),
                        'checkout_step': 2,
                        'event_category': 'Donation',
                        'event_label': 'Location ' + locationId,
                        'location_id': locationId
                    });
                }
            } else if (data.event === 'donation.complete') {
                // Catch the specific donation completion event
                const normalizedEvent = {
                    data: {
                        givebutter: {
                            ...data,
                            success: true // Force success flag
                        }
                    }
                };
                handleGiveButterSuccess(normalizedEvent);
            }
        }
    });

    // Listen for Native DOM events (fallback)
    document.addEventListener('givebutter:success', handleGiveButterSuccess);
    document.addEventListener('givebutter:form:success', handleGiveButterSuccess);
    
    // Expose handler globally
    window.givebutterSuccess = handleGiveButterSuccess;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGiveButterTracking);
} else {
    initGiveButterTracking();
}

