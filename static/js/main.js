/**
 * Pocket Portals - Main Initialization
 * Sets up event listeners and initializes controllers
 */

(function() {
    'use strict';

    /**
     * Initialize the application when DOM is ready
     */
    function init() {
        // Initialize DOM element references
        if (typeof window.initDOMElements === 'function') {
            window.initDOMElements();
        }

        const {
            submitBtn,
            actionInput,
            newGameBtn,
            sheetSubmitBtn,
            sheetActionInput,
            storyBox
        } = window.DOMElements;

        // ===== Event Listeners =====

        // Desktop submit button
        if (submitBtn) {
            submitBtn.addEventListener('click', function() {
                if (typeof window.submitAction === 'function') {
                    window.submitAction();
                }
            });
        }

        // Desktop action input - Enter key
        if (actionInput) {
            actionInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && typeof window.submitAction === 'function') {
                    window.submitAction();
                }
            });
        }

        // New game button (unified for mobile and desktop header)
        if (newGameBtn) {
            newGameBtn.addEventListener('click', function() {
                if (typeof window.newGame === 'function') {
                    window.newGame();
                }
            });
        }

        // Bottom sheet submit button
        if (sheetSubmitBtn) {
            sheetSubmitBtn.addEventListener('click', function() {
                if (typeof window.submitAction === 'function') {
                    window.submitAction();
                }
            });
        }

        // Bottom sheet action input - Enter key
        if (sheetActionInput) {
            sheetActionInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && typeof window.submitAction === 'function') {
                    window.submitAction();
                }
            });
        }

        // Begin button (event delegation for dynamically created button)
        if (storyBox) {
            storyBox.addEventListener('click', function(e) {
                if (e.target.id === 'begin-btn' || e.target.closest('#begin-btn')) {
                    if (typeof window.startNewAdventure === 'function') {
                        window.startNewAdventure(true);
                    }
                }
            });
        }

        // ===== Initialize Controllers =====

        if (window.BottomSheet && typeof window.BottomSheet.init === 'function') {
            window.BottomSheet.init();
        }

        if (window.GameHeader && typeof window.GameHeader.init === 'function') {
            window.GameHeader.init();
        }

        // ===== Reading Mode Toggle =====
        initReadingMode();

        // ===== Focus on Load =====
        if (actionInput) {
            actionInput.focus();
        }

        console.log('Pocket Portals initialized');
    }

    /**
     * Initialize reading mode toggle with localStorage persistence
     */
    function initReadingMode() {
        const readingToggle = document.getElementById('reading-toggle');

        if (!readingToggle) return;

        // Load saved preference
        const savedReadingMode = localStorage.getItem('readingMode') === 'true';

        if (savedReadingMode) {
            document.body.classList.add('reading-mode');
        }

        // Toggle reading mode on click
        readingToggle.addEventListener('click', function() {
            document.body.classList.toggle('reading-mode');
            const isActive = document.body.classList.contains('reading-mode');
            localStorage.setItem('readingMode', isActive);
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM is already ready
        init();
    }

})();
