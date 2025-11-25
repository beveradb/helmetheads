/**
 * GiveButter Widget Tracking Integration
 * Handles events from GiveButter iframes for Google Analytics 4 and Meta Pixel
 */

// Helper to get location parameter or default context
function getLocationContext() {
    if (window.location.search) {
        const urlParams = new URLSearchParams(window.location.search);
        const loc = urlParams.get('loc');
        if (loc) {
            console.log('📍 [GiveButter] Location context from URL param:', loc);
            return loc;
        }
    }
    // Fallback for homepage or no param
    const context = window.location.pathname === '/' ? 'homepage' : 'unknown';
    console.log('📍 [GiveButter] Location context (fallback):', context, 'pathname:', window.location.pathname);
    return context;
}

// Unified GiveButter Success Handler
function handleGiveButterSuccess(event) {
    console.log('🎯 [GiveButter] handleGiveButterSuccess called');
    console.log('🎯 [GiveButter] Raw event:', event);
    
    // Normalize data from CustomEvent or MessageEvent
    let data = event.detail || event.data;
    console.log('🎯 [GiveButter] Initial data (event.detail || event.data):', data);
    
    if (data && data.givebutter) {
        console.log('🎯 [GiveButter] Found nested givebutter object, unwrapping...');
        data = data.givebutter; // Handle postMessage wrapping
    }
    console.log('🎯 [GiveButter] Normalized data:', data);
    
    // Check for donation vs signup
    // 1. Explicit event type check (most reliable for this widget)
    // 2. Data check (fallback)
    const isExplicitDonationEvent = data.event === 'donation.complete';
    const hasDonationAmount = data && (data.amount > 0 || data.total > 0 || data.plan_id);
    
    console.log('🔍 [GiveButter] Decision Logic:');
    console.log('  - data.event:', data?.event);
    console.log('  - isExplicitDonationEvent:', isExplicitDonationEvent);
    console.log('  - data.amount:', data?.amount);
    console.log('  - data.total:', data?.total);
    console.log('  - data.plan_id:', data?.plan_id);
    console.log('  - hasDonationAmount:', hasDonationAmount);
    
    const isDonation = isExplicitDonationEvent || hasDonationAmount;
    console.log('💰 [GiveButter] IS DONATION:', isDonation);
    
    // Get location for analytics
    const locationId = getLocationContext();

    // Use 'total' if 'amount' is missing (GiveButter sometimes uses 'total')
    const donationAmount = parseFloat(data.amount || data.total || 0);
    console.log('💵 [GiveButter] Donation amount:', donationAmount);

    if (isDonation) {
        // --- DONATION TRACKING ---
        console.log('💳 [GiveButter] DONATION PATH - Tracking purchase events');
        
        if (typeof gtag !== 'undefined') {
            const gaParams = {
                'transaction_id': data.id || ('don_' + Date.now()),
                'value': donationAmount,
                'currency': 'USD',
                'event_category': 'Donation',
                'event_label': 'Location ' + locationId,
                'location_id': locationId
            };
            console.log('✅ [GA4] Calling gtag(\'event\', \'purchase\') with params:', gaParams);
            gtag('event', 'purchase', gaParams);
            console.log('✅ [GA4] Purchase event sent successfully');
        } else {
            console.warn('⚠️ [GA4] gtag is not defined - skipping Google Analytics tracking');
        }
        
        if (typeof fbq !== 'undefined') {
            const fbParams = {
                value: donationAmount,
                currency: 'USD',
                content_name: 'Bike Donation',
                content_type: 'donation',
                location_id: locationId
            };
            console.log('✅ [Meta] Calling fbq(\'track\', \'Purchase\') with params:', fbParams);
            fbq('track', 'Purchase', fbParams);
            console.log('✅ [Meta] Purchase event sent successfully');
        } else {
            console.warn('⚠️ [Meta] fbq is not defined - skipping Facebook Pixel tracking');
        }
        
    } else {
        // --- SIGNUP TRACKING ---
        console.log('📧 [GiveButter] SIGNUP PATH - Tracking email signup events');
        
        if (typeof gtag !== 'undefined') {
            const gaParams = {
                'event_category': 'Conversion',
                'event_label': 'Location ' + locationId,
                'location_id': locationId
            };
            console.log('✅ [GA4] Calling gtag(\'event\', \'email_signup\') with params:', gaParams);
            gtag('event', 'email_signup', gaParams);
            console.log('✅ [GA4] Email signup event sent successfully');
        } else {
            console.warn('⚠️ [GA4] gtag is not defined - skipping Google Analytics tracking');
        }
        
        if (typeof fbq !== 'undefined') {
            const fbParams = {
                location_id: locationId
            };
            console.log('✅ [Meta] Calling fbq(\'track\', \'Subscribe\') with params:', fbParams);
            fbq('track', 'Subscribe', fbParams);
            console.log('✅ [Meta] Subscribe event sent successfully');
        } else {
            console.warn('⚠️ [Meta] fbq is not defined - skipping Facebook Pixel tracking');
        }

        // Show local Thank You UI for signups (Donate page only)
        const thankYouMessage = document.getElementById('thank-you-message');
        const donationSection = document.getElementById('donation-section');
        
        if (thankYouMessage) {
            if (!thankYouMessage.classList.contains('show')) {
                console.log('💬 [GiveButter] Showing thank you message for signup');
                thankYouMessage.classList.add('show');
                thankYouMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Nudge towards donation after a delay
                setTimeout(function() {
                    if (donationSection) {
                        console.log('💬 [GiveButter] Scrolling to donation section after signup');
                        donationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 1200);
            } else {
                console.log('💬 [GiveButter] Thank you message already shown, skipping');
            }
        } else {
            console.log('💬 [GiveButter] No thank-you-message element found (normal for index.html)');
        }
    }
}

// Main Event Listener setup
function initGiveButterTracking() {
    console.log('🚀 [GiveButter] === Tracking Initialized ===');
    console.log('🚀 [GiveButter] Page:', window.location.pathname);
    console.log('🚀 [GiveButter] gtag available:', typeof gtag !== 'undefined');
    console.log('🚀 [GiveButter] fbq available:', typeof fbq !== 'undefined');

    // Listen for postMessage events from GiveButter iframe
    window.addEventListener('message', function(event) {
        // Log ALL postMessage events from GiveButter for debugging
        if (event.data && (event.data.givebutter || event.data.type?.includes('givebutter'))) {
            console.log('📨 [GiveButter] Received postMessage event:', event.data);
        }
        
        // Check for standard success events
        if (event.data && (
            event.data.type === 'givebutter:form:success' ||
            event.data.type === 'givebutter:success' ||
            (event.data.givebutter && event.data.givebutter.success)
        )) {
            console.log('🎉 [GiveButter] SUCCESS EVENT detected via postMessage');
            console.log('🎉 [GiveButter] Event type:', event.data.type);
            handleGiveButterSuccess(event);
        }

        // Check for intermediate donation events
        if (event.data && event.data.givebutter && event.data.event) {
            const data = event.data;
            const locationId = getLocationContext();

            if (data.event === 'donation.started') {
                console.log('🛒 [GiveButter] donation.started event - Begin Checkout');
                if (typeof gtag !== 'undefined') {
                    const gaParams = {
                        'currency': 'USD',
                        'value': parseFloat(data.total || 0),
                        'event_category': 'Donation',
                        'event_label': 'Location ' + locationId,
                        'location_id': locationId
                    };
                    console.log('✅ [GA4] Calling gtag(\'event\', \'begin_checkout\') with params:', gaParams);
                    gtag('event', 'begin_checkout', gaParams);
                } else {
                    console.warn('⚠️ [GA4] gtag not defined - skipping begin_checkout');
                }
            } else if (data.event === 'donation.button.next') {
                console.log('➡️ [GiveButter] donation.button.next event - Checkout Progress');
                if (typeof gtag !== 'undefined') {
                    const gaParams = {
                        'currency': 'USD',
                        'value': parseFloat(data.total || 0),
                        'checkout_step': 2,
                        'event_category': 'Donation',
                        'event_label': 'Location ' + locationId,
                        'location_id': locationId
                    };
                    console.log('✅ [GA4] Calling gtag(\'event\', \'checkout_progress\') with params:', gaParams);
                    gtag('event', 'checkout_progress', gaParams);
                } else {
                    console.warn('⚠️ [GA4] gtag not defined - skipping checkout_progress');
                }
            } else if (data.event === 'donation.complete') {
                console.log('✅ [GiveButter] donation.complete event detected!');
                // Catch the specific donation completion event
                const normalizedEvent = {
                    data: {
                        givebutter: {
                            ...data,
                            success: true // Force success flag
                        }
                    }
                };
                console.log('✅ [GiveButter] Normalizing donation.complete event and calling handler');
                handleGiveButterSuccess(normalizedEvent);
            }
        }
    });

    // Listen for Native DOM events (fallback)
    console.log('🎧 [GiveButter] Setting up DOM event listeners for fallback');
    document.addEventListener('givebutter:success', function(event) {
        console.log('🎉 [GiveButter] SUCCESS EVENT detected via DOM event: givebutter:success');
        handleGiveButterSuccess(event);
    });
    document.addEventListener('givebutter:form:success', function(event) {
        console.log('🎉 [GiveButter] SUCCESS EVENT detected via DOM event: givebutter:form:success');
        handleGiveButterSuccess(event);
    });
    
    // Expose handler globally
    window.givebutterSuccess = handleGiveButterSuccess;
    console.log('🌐 [GiveButter] Exposed window.givebutterSuccess() function globally');
    console.log('🚀 [GiveButter] === Setup Complete ===');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    console.log('⏳ [GiveButter] DOM still loading, waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', initGiveButterTracking);
} else {
    console.log('✅ [GiveButter] DOM already loaded, initializing immediately');
    initGiveButterTracking();
}

