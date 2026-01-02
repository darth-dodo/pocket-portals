/**
 * Tests for themes.js - Theme Controller
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    VALID_THEMES,
    DEFAULT_THEME,
    STORAGE_KEY,
    isValidTheme,
    getCurrentTheme,
    updateActiveOption,
    applyTheme,
    openModal,
    closeModal,
    setTheme,
    loadSavedTheme,
    resetThemeState,
    ThemeController
} from '../themes.js';

describe('Theme Controller', () => {
    beforeEach(() => {
        // Reset theme state before each test
        resetThemeState();
        // Reset document body
        document.body.innerHTML = '';
        // Reset document element attributes
        document.documentElement.removeAttribute('data-theme');
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Constants', () => {
        it('should have correct valid themes list', () => {
            expect(VALID_THEMES).toEqual(['rpg', 'modern', 'midnight', 'mono', 'ios']);
        });

        it('should have rpg as default theme', () => {
            expect(DEFAULT_THEME).toBe('rpg');
        });

        it('should have correct storage key', () => {
            expect(STORAGE_KEY).toBe('pocket-portals-theme');
        });
    });

    describe('isValidTheme', () => {
        it('should return true for valid themes', () => {
            VALID_THEMES.forEach(theme => {
                expect(isValidTheme(theme)).toBe(true);
            });
        });

        it('should return false for invalid theme', () => {
            expect(isValidTheme('invalid-theme')).toBe(false);
        });

        it('should return false for null', () => {
            expect(isValidTheme(null)).toBe(false);
        });

        it('should return false for undefined', () => {
            expect(isValidTheme(undefined)).toBe(false);
        });

        it('should return false for empty string', () => {
            expect(isValidTheme('')).toBe(false);
        });
    });

    describe('getCurrentTheme', () => {
        it('should return default theme initially', () => {
            expect(getCurrentTheme()).toBe(DEFAULT_THEME);
        });

        it('should return current theme after applying a new theme', () => {
            applyTheme('modern');
            expect(getCurrentTheme()).toBe('modern');
        });
    });

    describe('applyTheme', () => {
        it('should set data-theme attribute on document element', () => {
            applyTheme('midnight');
            expect(document.documentElement.getAttribute('data-theme')).toBe('midnight');
        });

        it('should update current theme', () => {
            applyTheme('ios');
            expect(getCurrentTheme()).toBe('ios');
        });

        it('should return true for valid theme', () => {
            const result = applyTheme('mono');
            expect(result).toBe(true);
        });

        it('should return false for invalid theme', () => {
            const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
            const result = applyTheme('invalid');
            expect(result).toBe(false);
            expect(warnSpy).toHaveBeenCalledWith('ThemeController: Invalid theme name:', 'invalid');
        });

        it('should not change theme when invalid theme is provided', () => {
            applyTheme('modern');
            vi.spyOn(console, 'warn').mockImplementation(() => {});
            applyTheme('invalid');
            expect(getCurrentTheme()).toBe('modern');
        });

        it('should call updateActiveOption', () => {
            document.body.innerHTML = `
                <div class="theme-option" data-theme-select="rpg"></div>
                <div class="theme-option" data-theme-select="modern"></div>
            `;
            applyTheme('modern');
            const modernOption = document.querySelector('[data-theme-select="modern"]');
            const rpgOption = document.querySelector('[data-theme-select="rpg"]');
            expect(modernOption.classList.contains('active')).toBe(true);
            expect(rpgOption.classList.contains('active')).toBe(false);
        });
    });

    describe('updateActiveOption', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <div class="theme-option" data-theme-select="rpg"></div>
                <div class="theme-option" data-theme-select="modern"></div>
                <div class="theme-option" data-theme-select="midnight"></div>
            `;
        });

        it('should add active class to current theme option', () => {
            applyTheme('modern');
            const modernOption = document.querySelector('[data-theme-select="modern"]');
            expect(modernOption.classList.contains('active')).toBe(true);
        });

        it('should remove active class from non-current theme options', () => {
            applyTheme('modern');
            const rpgOption = document.querySelector('[data-theme-select="rpg"]');
            const midnightOption = document.querySelector('[data-theme-select="midnight"]');
            expect(rpgOption.classList.contains('active')).toBe(false);
            expect(midnightOption.classList.contains('active')).toBe(false);
        });

        it('should handle empty theme options list', () => {
            document.body.innerHTML = '';
            expect(() => updateActiveOption()).not.toThrow();
        });
    });

    describe('openModal', () => {
        it('should add visible class to theme modal', () => {
            document.body.innerHTML = '<div id="theme-modal"></div>';
            openModal();
            const modal = document.getElementById('theme-modal');
            expect(modal.classList.contains('visible')).toBe(true);
        });

        it('should handle missing modal gracefully', () => {
            document.body.innerHTML = '';
            expect(() => openModal()).not.toThrow();
        });
    });

    describe('closeModal', () => {
        it('should remove visible class from theme modal', () => {
            document.body.innerHTML = '<div id="theme-modal" class="visible"></div>';
            closeModal();
            const modal = document.getElementById('theme-modal');
            expect(modal.classList.contains('visible')).toBe(false);
        });

        it('should handle missing modal gracefully', () => {
            document.body.innerHTML = '';
            expect(() => closeModal()).not.toThrow();
        });
    });

    describe('setTheme', () => {
        beforeEach(() => {
            document.body.innerHTML = '<div id="theme-modal" class="visible"></div>';
        });

        it('should apply theme to document', () => {
            setTheme('midnight');
            expect(document.documentElement.getAttribute('data-theme')).toBe('midnight');
        });

        it('should persist theme to localStorage', () => {
            setTheme('ios');
            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'ios');
        });

        it('should close the modal', () => {
            setTheme('mono');
            const modal = document.getElementById('theme-modal');
            expect(modal.classList.contains('visible')).toBe(false);
        });

        it('should return true for valid theme', () => {
            const result = setTheme('modern');
            expect(result).toBe(true);
        });

        it('should return false for invalid theme', () => {
            vi.spyOn(console, 'warn').mockImplementation(() => {});
            const result = setTheme('invalid');
            expect(result).toBe(false);
        });

        it('should not persist invalid theme to localStorage', () => {
            vi.spyOn(console, 'warn').mockImplementation(() => {});
            setTheme('invalid');
            expect(localStorage.setItem).not.toHaveBeenCalled();
        });
    });

    describe('loadSavedTheme', () => {
        it('should return saved theme from localStorage', () => {
            localStorage.getItem.mockReturnValue('midnight');
            const theme = loadSavedTheme();
            expect(theme).toBe('midnight');
        });

        it('should return default theme when no theme is saved', () => {
            localStorage.getItem.mockReturnValue(null);
            const theme = loadSavedTheme();
            expect(theme).toBe(DEFAULT_THEME);
        });

        it('should return default theme when saved theme is invalid', () => {
            localStorage.getItem.mockReturnValue('invalid-theme');
            const theme = loadSavedTheme();
            expect(theme).toBe(DEFAULT_THEME);
        });

        it('should call localStorage.getItem with correct key', () => {
            loadSavedTheme();
            expect(localStorage.getItem).toHaveBeenCalledWith(STORAGE_KEY);
        });
    });

    describe('resetThemeState', () => {
        it('should reset current theme to default', () => {
            applyTheme('midnight');
            resetThemeState();
            expect(getCurrentTheme()).toBe(DEFAULT_THEME);
        });
    });

    describe('ThemeController object', () => {
        it('should expose currentTheme getter', () => {
            applyTheme('modern');
            expect(ThemeController.currentTheme).toBe('modern');
        });

        it('should expose validThemes', () => {
            expect(ThemeController.validThemes).toEqual(VALID_THEMES);
        });

        it('should expose all methods', () => {
            expect(typeof ThemeController.init).toBe('function');
            expect(typeof ThemeController.isValidTheme).toBe('function');
            expect(typeof ThemeController.applyTheme).toBe('function');
            expect(typeof ThemeController.setTheme).toBe('function');
            expect(typeof ThemeController.updateActiveOption).toBe('function');
            expect(typeof ThemeController.openModal).toBe('function');
            expect(typeof ThemeController.closeModal).toBe('function');
            expect(typeof ThemeController.getCurrentTheme).toBe('function');
            expect(typeof ThemeController.setupEventListeners).toBe('function');
        });

        it('should have working isValidTheme method', () => {
            expect(ThemeController.isValidTheme('rpg')).toBe(true);
            expect(ThemeController.isValidTheme('invalid')).toBe(false);
        });
    });

    describe('window exports', () => {
        it('should expose ThemeController to window', () => {
            expect(window.ThemeController).toBe(ThemeController);
        });

        it('should expose individual functions to window', () => {
            expect(window.setTheme).toBe(setTheme);
            expect(window.applyTheme).toBe(applyTheme);
            expect(window.openModal).toBe(openModal);
            expect(window.closeModal).toBe(closeModal);
            expect(window.getCurrentTheme).toBe(getCurrentTheme);
            expect(window.isValidTheme).toBe(isValidTheme);
        });
    });

    describe('localStorage persistence', () => {
        it('should call localStorage.setItem when setting theme', () => {
            document.body.innerHTML = '<div id="theme-modal"></div>';

            setTheme('midnight');
            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'midnight');
        });

        it('should call localStorage.setItem for each theme change', () => {
            document.body.innerHTML = '<div id="theme-modal"></div>';

            setTheme('midnight');
            setTheme('ios');

            expect(localStorage.setItem).toHaveBeenCalledTimes(2);
            expect(localStorage.setItem).toHaveBeenNthCalledWith(1, STORAGE_KEY, 'midnight');
            expect(localStorage.setItem).toHaveBeenNthCalledWith(2, STORAGE_KEY, 'ios');
        });

        it('should load persisted theme from localStorage', () => {
            localStorage.getItem.mockReturnValue('mono');
            const loadedTheme = loadSavedTheme();
            expect(loadedTheme).toBe('mono');
            expect(localStorage.getItem).toHaveBeenCalledWith(STORAGE_KEY);
        });
    });

    describe('theme switching workflow', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <div id="theme-modal"></div>
                <div class="theme-option" data-theme-select="rpg"></div>
                <div class="theme-option" data-theme-select="modern"></div>
                <div class="theme-option" data-theme-select="midnight"></div>
                <div class="theme-option" data-theme-select="mono"></div>
                <div class="theme-option" data-theme-select="ios"></div>
            `;
        });

        it('should complete full theme switching workflow', () => {
            // Open modal
            openModal();
            expect(document.getElementById('theme-modal').classList.contains('visible')).toBe(true);

            // Set theme
            setTheme('midnight');

            // Verify theme is applied
            expect(document.documentElement.getAttribute('data-theme')).toBe('midnight');
            expect(getCurrentTheme()).toBe('midnight');

            // Verify theme is persisted
            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'midnight');

            // Verify modal is closed
            expect(document.getElementById('theme-modal').classList.contains('visible')).toBe(false);

            // Verify active option is updated
            const midnightOption = document.querySelector('[data-theme-select="midnight"]');
            expect(midnightOption.classList.contains('active')).toBe(true);
        });

        it('should switch between all valid themes', () => {
            VALID_THEMES.forEach(theme => {
                setTheme(theme);
                expect(getCurrentTheme()).toBe(theme);
                expect(document.documentElement.getAttribute('data-theme')).toBe(theme);
            });
        });
    });

    describe('all valid themes', () => {
        it('should handle rpg theme', () => {
            applyTheme('rpg');
            expect(getCurrentTheme()).toBe('rpg');
            expect(document.documentElement.getAttribute('data-theme')).toBe('rpg');
        });

        it('should handle modern theme', () => {
            applyTheme('modern');
            expect(getCurrentTheme()).toBe('modern');
            expect(document.documentElement.getAttribute('data-theme')).toBe('modern');
        });

        it('should handle midnight theme', () => {
            applyTheme('midnight');
            expect(getCurrentTheme()).toBe('midnight');
            expect(document.documentElement.getAttribute('data-theme')).toBe('midnight');
        });

        it('should handle mono theme', () => {
            applyTheme('mono');
            expect(getCurrentTheme()).toBe('mono');
            expect(document.documentElement.getAttribute('data-theme')).toBe('mono');
        });

        it('should handle ios theme', () => {
            applyTheme('ios');
            expect(getCurrentTheme()).toBe('ios');
            expect(document.documentElement.getAttribute('data-theme')).toBe('ios');
        });
    });
});
