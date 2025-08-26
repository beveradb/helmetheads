// Mobile navigation toggle
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a nav link
document.querySelectorAll('.nav-link').forEach(n => n.addEventListener('click', () => {
    hamburger.classList.remove('active');
    navMenu.classList.remove('active');
}));

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
    }
});

// Fundraising progress animation
function animateProgress() {
    const progressFill = document.getElementById('progress-fill');
    const raisedAmount = document.getElementById('raised-amount');
    const bikesFunded = document.getElementById('bikes-funded');
    
    const targetAmount = 2450;
    const goalAmount = 15000;
    const targetBikes = 8;
    const progressPercentage = (targetAmount / goalAmount) * 100;
    
    // Animate raised amount
    let currentAmount = 0;
    const amountInterval = setInterval(() => {
        currentAmount += 50;
        raisedAmount.textContent = `$${currentAmount.toLocaleString()}`;
        if (currentAmount >= targetAmount) {
            clearInterval(amountInterval);
            raisedAmount.textContent = `$${targetAmount.toLocaleString()}`;
        }
    }, 30);
    
    // Animate bikes funded
    let currentBikes = 0;
    const bikesInterval = setInterval(() => {
        currentBikes++;
        bikesFunded.textContent = currentBikes;
        if (currentBikes >= targetBikes) {
            clearInterval(bikesInterval);
        }
    }, 200);
    
    // Animate progress bar
    setTimeout(() => {
        progressFill.style.width = `${progressPercentage}%`;
    }, 500);
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            
            // Trigger fundraising animation when section comes into view
            if (entry.target.classList.contains('fundraising')) {
                animateProgress();
            }
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    // Add animation classes to elements
    const animatedElements = document.querySelectorAll('.about-card, .program-info, .leader-card, .stat-card, .tier');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Observe fundraising section
    const fundraisingSection = document.querySelector('.fundraising');
    if (fundraisingSection) {
        observer.observe(fundraisingSection);
    }
});

// Form submission handling
document.getElementById('signup-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(this);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Simple validation
    const requiredFields = ['studentName', 'grade', 'parentName', 'email', 'phone', 'experience'];
    const missingFields = requiredFields.filter(field => !data[field]);
    
    if (missingFields.length > 0) {
        alert('Please fill in all required fields.');
        return;
    }
    
    if (!data.commitment) {
        alert('Please confirm your commitment to the program.');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        alert('Please enter a valid email address.');
        return;
    }
    
    // Show success message
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<i class="fas fa-check"></i> Registration Submitted!';
    submitBtn.style.background = 'var(--accent-color)';
    submitBtn.disabled = true;
    
    // In a real application, you would send this data to your server
    console.log('Form submitted with data:', data);
    
    // Show success message
    setTimeout(() => {
        alert(`Thank you ${data.studentName}! Your registration has been submitted. We'll contact you at ${data.email} with next steps.`);
        
        // Reset form
        this.reset();
        submitBtn.innerHTML = originalText;
        submitBtn.style.background = '';
        submitBtn.disabled = false;
    }, 1500);
});

// Donation button interaction
document.getElementById('donate-btn').addEventListener('click', function() {
    // In a real application, this would integrate with a payment processor
    alert('Thank you for your interest in supporting Helmet Heads! Donation functionality would integrate with a payment processor like Stripe or PayPal in a live implementation.');
});

// Add loading animation to buttons
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!this.classList.contains('loading')) {
            this.classList.add('loading');
            setTimeout(() => {
                this.classList.remove('loading');
            }, 300);
        }
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const parallax = document.querySelector('.bike-illustration');
    const speed = scrolled * 0.2;
    
    if (parallax) {
        parallax.style.transform = `translateY(${speed}px)`;
    }
});

// Add floating animation to cards on hover
document.querySelectorAll('.about-card, .stat-card, .tier').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-10px)';
        this.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '';
    });
});

// Update progress text dynamically
function updateProgressText() {
    const progressText = document.querySelector('.progress-text');
    const currentAmount = 2450;
    const goalAmount = 15000;
    const percentage = Math.round((currentAmount / goalAmount) * 100);
    
    if (progressText) {
        progressText.textContent = `${percentage}% of our goal reached!`;
    }
}

// Call progress text update
updateProgressText();

// Add typing effect to hero title (optional enhancement)
function typeWriter(element, text, speed = 100) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Uncomment to enable typing effect on hero title
// window.addEventListener('load', () => {
//     const heroTitle = document.querySelector('.hero-title');
//     const originalText = heroTitle.textContent;
//     typeWriter(heroTitle, originalText, 50);
// });

// Add stagger animation to cards
function staggerAnimation(elements, delay = 100) {
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * delay);
    });
}

// Performance optimization: Debounce scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced scroll handler
const debouncedScrollHandler = debounce(() => {
    const scrolled = window.pageYOffset;
    const navbar = document.querySelector('.navbar');
    const parallax = document.querySelector('.bike-illustration');
    
    // Navbar background
    if (scrolled > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
    }
    
    // Parallax effect
    if (parallax) {
        const speed = scrolled * 0.2;
        parallax.style.transform = `translateY(${speed}px)`;
    }
}, 10);

// Replace the original scroll handler
window.removeEventListener('scroll', () => {});
window.addEventListener('scroll', debouncedScrollHandler);

// Add entrance animations for better UX
document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in animation to hero content
    const heroContent = document.querySelector('.hero-content');
    if (heroContent) {
        heroContent.style.opacity = '0';
        heroContent.style.transform = 'translateY(30px)';
        heroContent.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        
        setTimeout(() => {
            heroContent.style.opacity = '1';
            heroContent.style.transform = 'translateY(0)';
        }, 200);
    }
    
    // Add stagger animation to navigation items
    const navItems = document.querySelectorAll('.nav-link');
    navItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(-10px)';
        item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 100 + (index * 50));
    });
});