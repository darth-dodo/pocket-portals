/**
 * Pocket Portals - Main Initialization
 * Sets up event listeners and initializes controllers
 */

/**
 * Initialize the application when DOM is ready
 */
export function init() {
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
    } = window.DOMElements || {};

    // ===== Event Listeners =====

    // Desktop submit button
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            // Trigger haptic feedback for submit action
            if (typeof window.hapticFeedback === 'function') {
                window.hapticFeedback('light');
            }
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
            // Trigger haptic feedback for submit action
            if (typeof window.hapticFeedback === 'function') {
                window.hapticFeedback('light');
            }
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

    if (window.CharacterSheet && typeof window.CharacterSheet.init === 'function') {
        window.CharacterSheet.init();
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
export function initReadingMode() {
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

/**
 * Auto-initialize when DOM is ready (for browser script tag usage)
 */
export function autoInit() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM is already ready
        init();
    }
}

// Browser compatibility: expose to window and auto-initialize
if (typeof window !== 'undefined') {
    window.initApp = init;
    window.initReadingMode = initReadingMode;

    // Auto-initialize for script tag usage
    autoInit();
}
