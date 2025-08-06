/**
 * Modern UI JavaScript Utilities for CRM School
 * Provides enhanced interactivity, form validation, and accessibility features
 */

class ModernUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.setupFormValidation();
        this.setupAccessibility();
        this.setupAnimations();
        this.setupParticles();
    }

    // Theme Management
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        const body = document.body;
        const themeIcon = themeToggle.querySelector('i');

        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('theme') || 'light';
        body.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme, themeIcon);

        themeToggle.addEventListener('click', () => {
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.updateThemeIcon(newTheme, themeIcon);
            
            // Dispatch custom event for other components
            document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
        });
    }

    updateThemeIcon(theme, icon) {
        if (!icon) return;
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    // Form Validation
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            this.setupFormValidationForForm(form);
        });
    }

    setupFormValidationForForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Real-time validation
            input.addEventListener('input', (e) => {
                this.validateField(e.target);
            });

            // Blur validation
            input.addEventListener('blur', (e) => {
                this.validateField(e.target);
            });

            // Focus management
            input.addEventListener('focus', (e) => {
                this.handleFieldFocus(e.target);
            });
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                this.showFormErrors(form);
            }
        });
    }

    validateField(field) {
        const validators = this.getValidators(field);
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        for (const validator of validators) {
            const result = validator(value, field);
            if (!result.isValid) {
                isValid = false;
                message = result.message;
                break;
            }
        }

        this.updateFieldValidation(field, isValid, message);
        return isValid;
    }

    getValidators(field) {
        const validators = [];
        const type = field.type;
        const required = field.hasAttribute('required');
        const minLength = field.getAttribute('minlength');
        const maxLength = field.getAttribute('maxlength');
        const pattern = field.getAttribute('pattern');

        // Required validation
        if (required) {
            validators.push((value) => ({
                isValid: value.length > 0,
                message: 'This field is required'
            }));
        }

        // Email validation
        if (type === 'email') {
            validators.push((value) => ({
                isValid: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Please enter a valid email address'
            }));
        }

        // Phone validation
        if (field.name === 'username' || field.getAttribute('data-phone')) {
            validators.push((value) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                const phoneRegex = /^\d{10}$/;
                return {
                    isValid: emailRegex.test(value) || phoneRegex.test(value),
                    message: 'Please enter a valid email or 10-digit phone number'
                };
            });
        }

        // Password validation
        if (type === 'password') {
            validators.push((value) => ({
                isValid: value.length >= 6,
                message: 'Password must be at least 6 characters'
            }));
        }

        // Length validation
        if (minLength) {
            validators.push((value) => ({
                isValid: value.length >= parseInt(minLength),
                message: `Must be at least ${minLength} characters`
            }));
        }

        if (maxLength) {
            validators.push((value) => ({
                isValid: value.length <= parseInt(maxLength),
                message: `Must be no more than ${maxLength} characters`
            }));
        }

        // Pattern validation
        if (pattern) {
            validators.push((value) => ({
                isValid: new RegExp(pattern).test(value),
                message: field.getAttribute('data-pattern-message') || 'Invalid format'
            }));
        }

        return validators;
    }

    updateFieldValidation(field, isValid, message) {
        const validationElement = document.getElementById(`${field.id}-validation`);
        
        field.classList.remove('valid', 'invalid');
        if (validationElement) {
            validationElement.classList.remove('valid', 'invalid');
        }
        
        if (isValid) {
            field.classList.add('valid');
            if (validationElement) {
                validationElement.classList.add('valid');
                validationElement.textContent = '✓ Valid';
            }
        } else {
            field.classList.add('invalid');
            if (validationElement) {
                validationElement.classList.add('invalid');
                validationElement.textContent = message;
            }
        }
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    showFormErrors(form) {
        const firstInvalidField = form.querySelector('.invalid');
        if (firstInvalidField) {
            firstInvalidField.focus();
            this.showToast('Please correct the errors in the form', 'error');
        }
    }

    // Accessibility Features
    setupAccessibility() {
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupScreenReaderSupport();
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Escape key to close modals
            if (e.key === 'Escape') {
                this.closeModals();
            }

            // Enter key in password field to submit form
            if (e.key === 'Enter' && document.activeElement.type === 'password') {
                const form = document.activeElement.closest('form');
                if (form) {
                    form.requestSubmit();
                }
            }
        });
    }

    setupFocusManagement() {
        // Focus trap for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal[data-open="true"]');
                if (modal) {
                    this.handleFocusTrap(e, modal);
                }
            }
        });

        // Focus management for dynamic content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.setupFocusForElement(node);
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    setupFocusForElement(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        focusableElements.forEach(el => {
            el.addEventListener('focus', () => {
                el.classList.add('focused');
            });

            el.addEventListener('blur', () => {
                el.classList.remove('focused');
            });
        });
    }

    setupScreenReaderSupport() {
        // Live regions for dynamic content
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        document.body.appendChild(liveRegion);

        // Announce changes to screen readers
        this.announceToScreenReader = (message) => {
            liveRegion.textContent = message;
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        };
    }

    // Animation Management
    setupAnimations() {
        this.setupIntersectionObserver();
        this.setupScrollAnimations();
    }

    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        document.querySelectorAll('[data-animate]').forEach(el => {
            observer.observe(el);
        });
    }

    setupScrollAnimations() {
        let ticking = false;

        function updateAnimations() {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('[data-parallax]');

            parallaxElements.forEach(element => {
                const speed = element.getAttribute('data-parallax') || 0.5;
                const yPos = -(scrolled * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });

            ticking = false;
        }

        function requestTick() {
            if (!ticking) {
                requestAnimationFrame(updateAnimations);
                ticking = true;
            }
        }

        window.addEventListener('scroll', requestTick);
    }

    // Particle System
    setupParticles() {
        const particlesContainer = document.getElementById('particles');
        if (!particlesContainer) return;

        this.createParticles(particlesContainer);
        this.animateParticles(particlesContainer);
    }

    createParticles(container) {
        const particleCount = 50;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            const size = Math.random() * 4 + 2;
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight;
            const delay = Math.random() * 6;
            
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${x}px`;
            particle.style.top = `${y}px`;
            particle.style.animationDelay = `${delay}s`;
            
            container.appendChild(particle);
        }
    }

    animateParticles(container) {
        const particles = container.querySelectorAll('.particle');
        
        particles.forEach(particle => {
            particle.addEventListener('animationend', () => {
                // Reset particle position for continuous animation
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                particle.style.left = `${x}px`;
                particle.style.top = `${y}px`;
            });
        });
    }

    // Utility Methods
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Auto remove
        setTimeout(() => {
            this.hideToast(toast);
        }, duration);

        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.hideToast(toast);
        });
    }

    hideToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    closeModals() {
        const openModals = document.querySelectorAll('.modal[data-open="true"]');
        openModals.forEach(modal => {
            modal.setAttribute('data-open', 'false');
        });
    }

    handleFocusTrap(event, modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
            if (document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }

    // Password Toggle
    setupPasswordToggle() {
        const passwordToggles = document.querySelectorAll('[data-password-toggle]');
        
        passwordToggles.forEach(toggle => {
            const input = document.getElementById(toggle.getAttribute('data-password-toggle'));
            const icon = toggle.querySelector('i');
            
            if (!input || !icon) return;

            toggle.addEventListener('click', () => {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
                
                // Announce to screen readers
                this.announceToScreenReader(
                    type === 'password' ? 'Password hidden' : 'Password visible'
                );
            });
        });
    }

    // Loading States
    setupLoadingStates() {
        const forms = document.querySelectorAll('form[data-loading]');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    this.showLoadingState(submitBtn);
                }
            });
        });
    }

    showLoadingState(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="spinner"></div>';
        button.disabled = true;
        
        // Store original content for restoration
        button.setAttribute('data-original-content', originalText);
    }

    hideLoadingState(button) {
        const originalContent = button.getAttribute('data-original-content');
        if (originalContent) {
            button.innerHTML = originalContent;
            button.removeAttribute('data-original-content');
        }
        button.disabled = false;
    }
}

// Initialize Modern UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.modernUI = new ModernUI();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernUI;
} 