/**
 * Vitest Test Setup
 * Global setup for jsdom environment
 */

import { vi } from 'vitest';

// Mock navigator.vibrate for haptics tests
Object.defineProperty(navigator, 'vibrate', {
    value: vi.fn(() => true),
    writable: true,
    configurable: true
});

// Mock localStorage with proper spy functions
const localStorageMock = {
    store: {},
    getItem: vi.fn((key) => localStorageMock.store[key] || null),
    setItem: vi.fn((key, value) => {
        localStorageMock.store[key] = String(value);
    }),
    removeItem: vi.fn((key) => {
        delete localStorageMock.store[key];
    }),
    clear: vi.fn(() => {
        localStorageMock.store = {};
    }),
    get length() {
        return Object.keys(localStorageMock.store).length;
    },
    key: vi.fn((index) => {
        const keys = Object.keys(localStorageMock.store);
        return keys[index] || null;
    })
};

Object.defineProperty(global, 'localStorage', {
    value: localStorageMock,
    writable: true,
    configurable: true
});

// Mock console.debug to avoid noise in tests
vi.spyOn(console, 'debug').mockImplementation(() => {});

// Reset mocks before each test
beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.store = {};
});
