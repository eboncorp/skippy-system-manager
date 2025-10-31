/**
 * ==========================================================================
 * LOUISVILLE VOTER EDUCATION GLOSSARY - INTERACTIVE FUNCTIONALITY
 * Enhances glossary terms with mobile-friendly behavior and analytics
 * Version 2.1.0 | October 29, 2025
 * ==========================================================================
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        termClass: 'glossary-term',
        activeClass: 'active',
        clickModeClass: 'glossary-click-mode',
        mobileBreakpoint: 768,
        analyticsEnabled: true,
        closeOnOutsideClick: true,
        keyboardNavigation: true
    };
    
    /**
     * Initialize glossary functionality when DOM is ready
     */
    function init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupGlossary);
        } else {
            setupGlossary();
        }
    }
    
    /**
     * Main setup function
     */
    function setupGlossary() {
        // Detect if we're on a touch device
        const isTouchDevice = detectTouchDevice();
        
        // Enable click mode on mobile/touch devices
        if (isTouchDevice || window.innerWidth < CONFIG.mobileBreakpoint) {
            enableClickMode();
        }
        
        // Setup event listeners
        setupEventListeners();
        
        // Enable keyboard navigation
        if (CONFIG.keyboardNavigation) {
            setupKeyboardNav();
        }
        
        // Track glossary usage for analytics
        if (CONFIG.analyticsEnabled) {
            setupAnalytics();
        }
        
        console.log('Glossary system initialized');
    }
    
    /**
     * Detect if user is on a touch device
     */
    function detectTouchDevice() {
        return (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0));
    }
    
    /**
     * Enable click-to-show mode for mobile
     */
    function enableClickMode() {
        document.body.classList.add(CONFIG.clickModeClass);
        
        // Add click handlers to all glossary terms
        const terms = document.querySelectorAll('.' + CONFIG.termClass);
        terms.forEach(term => {
            term.addEventListener('click', handleTermClick);
            term.addEventListener('touchstart', handleTermClick, { passive: true });
        });
        
        // Close tooltips when clicking outside
        if (CONFIG.closeOnOutsideClick) {
            document.addEventListener('click', handleOutsideClick);
            document.addEventListener('touchstart', handleOutsideClick, { passive: true });
        }
    }
    
    /**
     * Handle clicking on a glossary term
     */
    function handleTermClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const term = e.currentTarget;
        const wasActive = term.classList.contains(CONFIG.activeClass);
        
        // Close all other open tooltips
        closeAllTooltips();
        
        // Toggle this tooltip
        if (!wasActive) {
            term.classList.add(CONFIG.activeClass);
            
            // Track this interaction
            trackTermView(term);
            
            // Ensure tooltip is visible on screen
            ensureTooltipVisible(term);
        }
    }
    
    /**
     * Handle clicking outside glossary terms to close tooltips
     */
    function handleOutsideClick(e) {
        if (!e.target.classList.contains(CONFIG.termClass)) {
            closeAllTooltips();
        }
    }
    
    /**
     * Close all open tooltips
     */
    function closeAllTooltips() {
        const activeTerms = document.querySelectorAll('.' + CONFIG.termClass + '.' + CONFIG.activeClass);
        activeTerms.forEach(term => {
            term.classList.remove(CONFIG.activeClass);
        });
    }
    
    /**
     * Ensure tooltip is visible on screen (adjust scroll if needed)
     */
    function ensureTooltipVisible(term) {
        setTimeout(() => {
            const rect = term.getBoundingClientRect();
            const tooltipHeight = 150; // Approximate tooltip height
            
            // If tooltip would go above viewport, scroll up
            if (rect.top < tooltipHeight) {
                window.scrollBy({
                    top: rect.top - tooltipHeight - 20,
                    behavior: 'smooth'
                });
            }
        }, 100);
    }
    
    /**
     * Setup general event listeners
     */
    function setupEventListeners() {
        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                // Switch between hover and click mode based on screen size
                const shouldBeClickMode = window.innerWidth < CONFIG.mobileBreakpoint;
                const isClickMode = document.body.classList.contains(CONFIG.clickModeClass);
                
                if (shouldBeClickMode && !isClickMode) {
                    enableClickMode();
                } else if (!shouldBeClickMode && isClickMode) {
                    disableClickMode();
                }
            }, 250);
        });
    }
    
    /**
     * Disable click mode (enable hover mode)
     */
    function disableClickMode() {
        document.body.classList.remove(CONFIG.clickModeClass);
        
        // Remove click handlers
        const terms = document.querySelectorAll('.' + CONFIG.termClass);
        terms.forEach(term => {
            term.removeEventListener('click', handleTermClick);
            term.removeEventListener('touchstart', handleTermClick);
        });
        
        document.removeEventListener('click', handleOutsideClick);
        document.removeEventListener('touchstart', handleOutsideClick);
    }
    
    /**
     * Setup keyboard navigation for accessibility
     */
    function setupKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            // Escape key closes all tooltips
            if (e.key === 'Escape') {
                closeAllTooltips();
            }
            
            // Tab navigation
            if (e.key === 'Tab') {
                const activeElement = document.activeElement;
                if (activeElement.classList.contains(CONFIG.termClass)) {
                    // Show tooltip when focused via keyboard
                    closeAllTooltips();
                    activeElement.classList.add(CONFIG.activeClass);
                }
            }
            
            // Enter or Space to toggle tooltip
            if ((e.key === 'Enter' || e.key === ' ') && 
                document.activeElement.classList.contains(CONFIG.termClass)) {
                e.preventDefault();
                handleTermClick({ 
                    currentTarget: document.activeElement,
                    preventDefault: () => {},
                    stopPropagation: () => {}
                });
            }
        });
    }
    
    /**
     * Setup analytics tracking
     */
    function setupAnalytics() {
        const terms = document.querySelectorAll('.' + CONFIG.termClass);
        
        terms.forEach(term => {
            // Track on hover (desktop)
            term.addEventListener('mouseenter', () => {
                if (!document.body.classList.contains(CONFIG.clickModeClass)) {
                    trackTermView(term);
                }
            });
        });
    }
    
    /**
     * Track when a glossary term is viewed
     */
    function trackTermView(term) {
        const termName = term.getAttribute('data-term') || term.textContent;
        
        // Google Analytics 4
        if (typeof gtag !== 'undefined') {
            gtag('event', 'glossary_term_view', {
                'term_name': termName,
                'page_path': window.location.pathname
            });
        }
        
        // Google Analytics Universal
        if (typeof ga !== 'undefined') {
            ga('send', 'event', 'Glossary', 'View', termName);
        }
        
        // Log to console for debugging
        console.log('Glossary term viewed:', termName);
    }
    
    /**
     * Public API
     */
    window.LouisvilleGlossary = {
        closeAll: closeAllTooltips,
        trackTerm: trackTermView,
        enableClickMode: enableClickMode,
        disableClickMode: disableClickMode
    };
    
    // Initialize on load
    init();
    
})();

/**
 * ==========================================================================
 * WORDPRESS INTEGRATION HELPER
 * For sites using WordPress with glossary plugin
 * ==========================================================================
 */

/**
 * Automatically convert glossary links from plugin to use our styling
 */
function initializeWordPressGlossary() {
    // Wait for WordPress to load
    jQuery(document).ready(function($) {
        // Find glossary links added by plugin
        $('a[data-glossary], .glossary-link').each(function() {
            const $link = $(this);
            const title = $link.attr('data-definition') || $link.attr('title');
            const term = $link.attr('data-term') || $link.text();
            
            // Convert to span with our class
            const $span = $('<span>', {
                'class': 'glossary-term',
                'data-term': term,
                'title': title,
                'text': $link.text()
            });
            
            $link.replaceWith($span);
        });
        
        // Reinitialize our glossary system
        if (window.LouisvilleGlossary) {
            console.log('Reinitialized glossary for WordPress content');
        }
    });
}

// Run WordPress integration if jQuery is available
if (typeof jQuery !== 'undefined') {
    initializeWordPressGlossary();
}

/**
 * ==========================================================================
 * USAGE ANALYTICS DASHBOARD HELPER
 * Track which terms are most viewed/needed
 * ==========================================================================
 */

/**
 * Get glossary usage statistics
 * Useful for campaign to see which terms voters need most
 */
function getGlossaryStats() {
    // Retrieve from localStorage
    const stats = JSON.parse(localStorage.getItem('glossary_stats') || '{}');
    
    // Sort by view count
    const sorted = Object.entries(stats)
        .sort((a, b) => b[1] - a[1])
        .map(([term, views]) => ({ term, views }));
    
    console.table(sorted);
    return sorted;
}

/**
 * Clear glossary statistics
 */
function clearGlossaryStats() {
    localStorage.removeItem('glossary_stats');
    console.log('Glossary statistics cleared');
}

// Make available globally for debugging
window.getGlossaryStats = getGlossaryStats;
window.clearGlossaryStats = clearGlossaryStats;

/**
 * ==========================================================================
 * IMPLEMENTATION NOTES
 * ==========================================================================
 * 
 * To use this script:
 * 
 * 1. Include this file in your HTML:
 *    <script src="glossary-interactive.js"></script>
 * 
 * 2. Include the CSS file:
 *    <link rel="stylesheet" href="glossary-styles.css">
 * 
 * 3. Use proper HTML structure for terms:
 *    <span class="glossary-term" 
 *          data-term="participatory-budgeting"
 *          title="Democratic process where...">
 *      participatory budgeting
 *    </span>
 * 
 * 4. For WordPress, ensure jQuery is loaded first
 * 
 * 5. For analytics, ensure Google Analytics is configured
 * 
 * ==========================================================================
 */
