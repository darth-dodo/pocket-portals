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

        // ===== Keyboard Shortcuts for Choice Selection =====
        initKeyboardShortcuts();

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

    /**
     * Initialize keyboard shortcuts for choice selection
     * Number keys 1-4 select corresponding choices when visible and not loading
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Skip if user is typing in an input field
            const activeElement = document.activeElement;
            if (activeElement && (
                activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.isContentEditable
            )) {
                return;
            }

            // Check if choices are available and not loading
            const state = window.GameState;
            if (!state || state.isLoading) {
                return;
            }

            // Check if choices section is visible
            const choicesSection = window.DOMElements && window.DOMElements.choicesSection;
            if (!choicesSection || choicesSection.classList.contains('hidden')) {
                return;
            }

            // Map number keys to choice indices
            const keyToIndex = {
                '1': 0,
                '2': 1,
                '3': 2,
                '4': 3
            };

            const choiceIndex = keyToIndex[e.key];

            // Check if valid key and choice exists at that index
            if (choiceIndex !== undefined && state.currentChoices && state.currentChoices.length > choiceIndex) {
                e.preventDefault();
                if (typeof window.selectChoice === 'function') {
                    // selectChoice expects 1-indexed choice number
                    window.selectChoice(choiceIndex + 1);
                }
            }
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
