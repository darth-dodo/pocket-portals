/**
 * Tests for haptics.js
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    HapticPresets,
    isHapticSupported,
    hapticFeedback,
    hapticPattern,
    cancelHaptic
} from '../haptics.js';

describe('HapticPresets', () => {
    it('should have correct preset values', () => {
        expect(HapticPresets.light).toBe(10);
        expect(HapticPresets.medium).toBe(20);
        expect(HapticPresets.heavy).toBe(30);
        expect(HapticPresets.snap).toBe(15);
    });
});

describe('isHapticSupported', () => {
    it('should return true when vibrate is available', () => {
        expect(isHapticSupported()).toBe(true);
    });

    it('should return false when vibrate is not available', () => {
        const originalVibrate = navigator.vibrate;
        delete navigator.vibrate;

        expect(isHapticSupported()).toBe(false);

        // Restore
        Object.defineProperty(navigator, 'vibrate', {
            value: originalVibrate,
            writable: true,
            configurable: true
        });
    });
});

describe('hapticFeedback', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should trigger vibration with light preset', () => {
        const result = hapticFeedback('light');

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(10);
    });

    it('should trigger vibration with medium preset', () => {
        const result = hapticFeedback('medium');

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(20);
    });

    it('should trigger vibration with heavy preset', () => {
        const result = hapticFeedback('heavy');

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(30);
    });

    it('should trigger vibration with snap preset', () => {
        const result = hapticFeedback('snap');

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(15);
    });

    it('should default to light preset for unknown type', () => {
        const result = hapticFeedback('unknown');

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(10);
    });

    it('should return false when vibration is not supported', () => {
        const originalVibrate = navigator.vibrate;
        delete navigator.vibrate;

        const result = hapticFeedback('light');

        expect(result).toBe(false);

        // Restore
        Object.defineProperty(navigator, 'vibrate', {
            value: originalVibrate,
            writable: true,
            configurable: true
        });
    });

    it('should return false and log when vibrate throws', () => {
        navigator.vibrate = vi.fn(() => {
            throw new Error('Vibration failed');
        });

        const result = hapticFeedback('light');

        expect(result).toBe(false);
        expect(console.debug).toHaveBeenCalled();

        // Restore
        navigator.vibrate = vi.fn(() => true);
    });
});

describe('hapticPattern', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should trigger vibration with custom pattern', () => {
        const pattern = [100, 50, 100];
        const result = hapticPattern(pattern);

        expect(result).toBe(true);
        expect(navigator.vibrate).toHaveBeenCalledWith(pattern);
    });

    it('should return false when vibration is not supported', () => {
        const originalVibrate = navigator.vibrate;
        delete navigator.vibrate;

        const result = hapticPattern([100, 50]);

        expect(result).toBe(false);

        // Restore
        Object.defineProperty(navigator, 'vibrate', {
            value: originalVibrate,
            writable: true,
            configurable: true
        });
    });

    it('should return false and log when vibrate throws', () => {
        navigator.vibrate = vi.fn(() => {
            throw new Error('Pattern failed');
        });

        const result = hapticPattern([100]);

        expect(result).toBe(false);
        expect(console.debug).toHaveBeenCalled();

        // Restore
        navigator.vibrate = vi.fn(() => true);
    });
});

describe('cancelHaptic', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should cancel vibration by calling vibrate(0)', () => {
        cancelHaptic();

        expect(navigator.vibrate).toHaveBeenCalledWith(0);
    });

    it('should not throw when vibration is not supported', () => {
        const originalVibrate = navigator.vibrate;
        delete navigator.vibrate;

        expect(() => cancelHaptic()).not.toThrow();

        // Restore
        Object.defineProperty(navigator, 'vibrate', {
            value: originalVibrate,
            writable: true,
            configurable: true
        });
    });
});
