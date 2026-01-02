/**
 * Pocket Portals - Haptic Feedback
 * Provides vibration feedback for mobile interactions
 */

(function() {
    'use strict';

    /**
     * Haptic feedback duration presets in milliseconds
     */
    const HapticPresets = {
        light: 10,    // Light tap - choice buttons, submit
        medium: 20,   // Medium tap - combat actions
        heavy: 30,    // Heavy tap - critical actions (reserved)
        snap: 15      // Snap feedback - bottom sheet snapping
    };

    /**
     * Check if the Vibration API is supported
     * @returns {boolean} True if vibration is supported
     */
    function isHapticSupported() {
        return 'vibrate' in navigator;
    }

    /**
     * Trigger haptic feedback
     * @param {string} type - Feedback type: 'light', 'medium', 'heavy', 'snap'
     * @returns {boolean} True if vibration was triggered
     */
    function hapticFeedback(type) {
        if (!isHapticSupported()) {
            return false;
        }

        const duration = HapticPresets[type] || HapticPresets.light;

        try {
            navigator.vibrate(duration);
            return true;
        } catch (error) {
            // Silently fail - haptic feedback is non-critical
            console.debug('Haptic feedback failed:', error);
            return false;
        }
    }

    /**
     * Trigger a custom vibration pattern
     * @param {number[]} pattern - Array of vibration/pause durations in ms
     * @returns {boolean} True if vibration was triggered
     */
    function hapticPattern(pattern) {
        if (!isHapticSupported()) {
            return false;
        }

        try {
            navigator.vibrate(pattern);
            return true;
        } catch (error) {
            console.debug('Haptic pattern failed:', error);
            return false;
        }
    }

    /**
     * Cancel any ongoing vibration
     */
    function cancelHaptic() {
        if (isHapticSupported()) {
            navigator.vibrate(0);
        }
    }

    // Expose to window
    window.hapticFeedback = hapticFeedback;
    window.hapticPattern = hapticPattern;
    window.cancelHaptic = cancelHaptic;
    window.isHapticSupported = isHapticSupported;

})();
