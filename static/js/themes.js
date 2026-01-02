/**
 * Pocket Portals - Theme Controller
 * Handles theme switching with localStorage persistence
 */

/**
 * List of valid theme names
 */
export const VALID_THEMES = ['rpg', 'modern', 'midnight', 'mono', 'ios'];

/**
 * Default theme to use when no theme is saved
 */
export const DEFAULT_THEME = 'rpg';

/**
 * LocalStorage key for theme persistence
 */
export const STORAGE_KEY = 'pocket-portals-theme';

/**
 * Current active theme (module-level state)
 */
let currentTheme = DEFAULT_THEME;

/**
 * Check if a theme name is valid
 * @param {string|null} themeName - Theme name to validate
 * @returns {boolean} True if theme is valid
 */
export function isValidTheme(themeName) {
    return Boolean(themeName && VALID_THEMES.includes(themeName));
}

/**
 * Get the current theme name
 * @returns {string} Current theme name
 */
export function getCurrentTheme() {
    return currentTheme;
}

/**
 * Update the active state on theme options in the DOM
 */
export function updateActiveOption() {
    const themeOptions = document.querySelectorAll('.theme-option');

    themeOptions.forEach(function(option) {
        const optionTheme = option.getAttribute('data-theme-select');
        if (optionTheme === currentTheme) {
            option.classList.add('active');
        } else {
            option.classList.remove('active');
        }
    });
}

/**
 * Apply a theme to the document without persisting
 * @param {string} themeName - Theme name to apply
 * @returns {boolean} True if theme was applied successfully
 */
export function applyTheme(themeName) {
    if (!isValidTheme(themeName)) {
        console.warn('ThemeController: Invalid theme name:', themeName);
        return false;
    }

    document.documentElement.setAttribute('data-theme', themeName);
    currentTheme = themeName;
    updateActiveOption();
    return true;
}

/**
 * Open the theme selector modal
 */
export function openModal() {
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.classList.add('visible');
    }
}

/**
 * Close the theme selector modal
 */
export function closeModal() {
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.classList.remove('visible');
    }
}

/**
 * Set and persist a theme
 * @param {string} themeName - Theme name to set
 * @returns {boolean} True if theme was set successfully
 */
export function setTheme(themeName) {
    if (!isValidTheme(themeName)) {
        console.warn('ThemeController: Invalid theme name:', themeName);
        return false;
    }

    // Apply theme
    applyTheme(themeName);

    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, themeName);

    // Close modal after selection
    closeModal();

    return true;
}

/**
 * Load saved theme from localStorage
 * @returns {string} The loaded theme name (or default if none saved)
 */
export function loadSavedTheme() {
    const savedTheme = localStorage.getItem(STORAGE_KEY);
    return isValidTheme(savedTheme) ? savedTheme : DEFAULT_THEME;
}

/**
 * Set up event listeners for theme controls
 */
export function setupEventListeners() {
    // Settings button opens modal (unified for mobile and desktop)
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            openModal();
        });
    }

    // Close button closes modal
    const closeBtn = document.getElementById('theme-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            closeModal();
        });
    }

    // Theme options select theme
    const themeOptions = document.querySelectorAll('.theme-option');
    themeOptions.forEach(function(option) {
        option.addEventListener('click', function() {
            const themeName = this.getAttribute('data-theme-select');
            if (themeName) {
                setTheme(themeName);
            }
        });
    });

    // Clicking overlay closes modal
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            // Only close if clicking the overlay, not the modal content
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Escape key closes modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

/**
 * Initialize the theme system
 * Loads saved theme and sets up event listeners
 */
export function initTheme() {
    // Load saved theme from localStorage
    currentTheme = loadSavedTheme();

    // Apply theme to document
    applyTheme(currentTheme);

    // Set up event listeners
    setupEventListeners();
}

/**
 * Reset theme state to default (useful for testing)
 */
export function resetThemeState() {
    currentTheme = DEFAULT_THEME;
}

/**
 * ThemeController object for backward compatibility
 * Mirrors the original IIFE interface
 */
export const ThemeController = {
    get currentTheme() {
        return getCurrentTheme();
    },
    validThemes: VALID_THEMES,
    init: initTheme,
    isValidTheme,
    applyTheme,
    setTheme,
    updateActiveOption,
    openModal,
    closeModal,
    getCurrentTheme,
    setupEventListeners
};

// Browser compatibility: expose to window for script tag usage
if (typeof window !== 'undefined') {
    window.ThemeController = ThemeController;
    window.initTheme = initTheme;
    window.setTheme = setTheme;
    window.applyTheme = applyTheme;
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.getCurrentTheme = getCurrentTheme;
    window.isValidTheme = isValidTheme;

    // Auto-initialize when DOM is ready (maintains original behavior)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
        });
    } else {
        // DOM is already ready
        initTheme();
    }
}
