/**
 * Pocket Portals - Theme Controller
 * Handles theme switching with localStorage persistence
 */

(function() {
    'use strict';

    // ===== Theme Controller =====
    const ThemeController = {
        currentTheme: 'rpg',
        validThemes: ['rpg', 'modern', 'midnight', 'mono', 'ios'],

        /**
         * Initialize the theme system
         * Loads saved theme and sets up event listeners
         */
        init: function() {
            // Load saved theme from localStorage
            const savedTheme = localStorage.getItem('pocket-portals-theme');
            this.currentTheme = this.isValidTheme(savedTheme) ? savedTheme : 'rpg';

            // Apply theme to document
            this.applyTheme(this.currentTheme);

            // Set up event listeners
            this.setupEventListeners();
        },

        /**
         * Check if a theme name is valid
         * @param {string|null} themeName - Theme name to validate
         * @returns {boolean} True if theme is valid
         */
        isValidTheme: function(themeName) {
            return themeName && this.validThemes.includes(themeName);
        },

        /**
         * Apply a theme to the document
         * @param {string} themeName - Theme name to apply
         */
        applyTheme: function(themeName) {
            if (!this.isValidTheme(themeName)) {
                console.warn('ThemeController: Invalid theme name:', themeName);
                return;
            }

            document.documentElement.setAttribute('data-theme', themeName);
            this.currentTheme = themeName;
            this.updateActiveOption();
        },

        /**
         * Set and persist a theme
         * @param {string} themeName - Theme name to set
         */
        setTheme: function(themeName) {
            if (!this.isValidTheme(themeName)) {
                console.warn('ThemeController: Invalid theme name:', themeName);
                return;
            }

            // Apply theme
            this.applyTheme(themeName);

            // Save to localStorage
            localStorage.setItem('pocket-portals-theme', themeName);

            // Close modal after selection
            this.closeModal();
        },

        /**
         * Update the active state on theme options
         */
        updateActiveOption: function() {
            const themeOptions = document.querySelectorAll('.theme-option');

            themeOptions.forEach(function(option) {
                const optionTheme = option.getAttribute('data-theme-select');
                if (optionTheme === this.currentTheme) {
                    option.classList.add('active');
                } else {
                    option.classList.remove('active');
                }
            }, this);
        },

        /**
         * Open the theme selector modal
         */
        openModal: function() {
            const modal = document.getElementById('theme-modal');
            if (modal) {
                modal.classList.add('visible');
            }
        },

        /**
         * Close the theme selector modal
         */
        closeModal: function() {
            const modal = document.getElementById('theme-modal');
            if (modal) {
                modal.classList.remove('visible');
            }
        },

        /**
         * Get the current theme name
         * @returns {string} Current theme name
         */
        getCurrentTheme: function() {
            return this.currentTheme;
        },

        /**
         * Set up event listeners for theme controls
         */
        setupEventListeners: function() {
            const self = this;

            // Settings button opens modal (unified for mobile and desktop)
            const settingsBtn = document.getElementById('settings-btn');
            if (settingsBtn) {
                settingsBtn.addEventListener('click', function() {
                    self.openModal();
                });
            }

            // Close button closes modal
            const closeBtn = document.getElementById('theme-modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    self.closeModal();
                });
            }

            // Theme options select theme
            const themeOptions = document.querySelectorAll('.theme-option');
            themeOptions.forEach(function(option) {
                option.addEventListener('click', function() {
                    const themeName = this.getAttribute('data-theme-select');
                    if (themeName) {
                        self.setTheme(themeName);
                    }
                });
            });

            // Clicking overlay closes modal
            const modal = document.getElementById('theme-modal');
            if (modal) {
                modal.addEventListener('click', function(e) {
                    // Only close if clicking the overlay, not the modal content
                    if (e.target === modal) {
                        self.closeModal();
                    }
                });
            }

            // Escape key closes modal
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    self.closeModal();
                }
            });
        }
    };

    // Expose controller to window
    window.ThemeController = ThemeController;

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            ThemeController.init();
        });
    } else {
        // DOM is already ready
        ThemeController.init();
    }

})();
