/**
 * Tests for main.js - Main Initialization
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { init, initReadingMode, autoInit } from '../main.js';

describe('Main Initialization', () => {
    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = '';
        document.body.className = '';

        // Reset window mocks
        window.DOMElements = {};
        window.initDOMElements = vi.fn();
        window.hapticFeedback = vi.fn();
        window.submitAction = vi.fn();
        window.newGame = vi.fn();
        window.startNewAdventure = vi.fn();
        window.BottomSheet = { init: vi.fn() };
        window.GameHeader = { init: vi.fn() };

        // Reset localStorage mock
        localStorage.getItem.mockReset();
        localStorage.setItem.mockReset();
    });

    describe('init', () => {
        it('should call initDOMElements if available', () => {
            init();
            expect(window.initDOMElements).toHaveBeenCalled();
        });

        it('should not throw if initDOMElements is not a function', () => {
            window.initDOMElements = 'not a function';
            expect(() => init()).not.toThrow();
        });

        it('should initialize BottomSheet controller', () => {
            init();
            expect(window.BottomSheet.init).toHaveBeenCalled();
        });

        it('should initialize GameHeader controller', () => {
            init();
            expect(window.GameHeader.init).toHaveBeenCalled();
        });

        it('should not throw if controllers are missing', () => {
            window.BottomSheet = null;
            window.GameHeader = null;
            expect(() => init()).not.toThrow();
        });
    });

    describe('submit button event listeners', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <button id="submit-btn"></button>
                <input id="action-input" />
            `;
            window.DOMElements = {
                submitBtn: document.getElementById('submit-btn'),
                actionInput: document.getElementById('action-input')
            };
        });

        it('should trigger haptic feedback and submitAction on submit button click', () => {
            init();
            const submitBtn = document.getElementById('submit-btn');
            submitBtn.click();

            expect(window.hapticFeedback).toHaveBeenCalledWith('light');
            expect(window.submitAction).toHaveBeenCalled();
        });

        it('should trigger submitAction on Enter key in action input', () => {
            init();
            const actionInput = document.getElementById('action-input');
            const event = new KeyboardEvent('keypress', { key: 'Enter' });
            actionInput.dispatchEvent(event);

            expect(window.submitAction).toHaveBeenCalled();
        });

        it('should not trigger submitAction on other keys', () => {
            init();
            const actionInput = document.getElementById('action-input');
            const event = new KeyboardEvent('keypress', { key: 'a' });
            actionInput.dispatchEvent(event);

            expect(window.submitAction).not.toHaveBeenCalled();
        });

        it('should focus action input on init', () => {
            init();
            const actionInput = document.getElementById('action-input');
            expect(document.activeElement).toBe(actionInput);
        });
    });

    describe('new game button', () => {
        beforeEach(() => {
            document.body.innerHTML = '<button id="new-game-btn"></button>';
            window.DOMElements = {
                newGameBtn: document.getElementById('new-game-btn')
            };
        });

        it('should call newGame on click', () => {
            init();
            const newGameBtn = document.getElementById('new-game-btn');
            newGameBtn.click();

            expect(window.newGame).toHaveBeenCalled();
        });
    });

    describe('bottom sheet elements', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <button id="sheet-submit-btn"></button>
                <input id="sheet-action-input" />
            `;
            window.DOMElements = {
                sheetSubmitBtn: document.getElementById('sheet-submit-btn'),
                sheetActionInput: document.getElementById('sheet-action-input')
            };
        });

        it('should trigger haptic feedback and submitAction on sheet submit click', () => {
            init();
            const sheetSubmitBtn = document.getElementById('sheet-submit-btn');
            sheetSubmitBtn.click();

            expect(window.hapticFeedback).toHaveBeenCalledWith('light');
            expect(window.submitAction).toHaveBeenCalled();
        });

        it('should trigger submitAction on Enter key in sheet action input', () => {
            init();
            const sheetActionInput = document.getElementById('sheet-action-input');
            const event = new KeyboardEvent('keypress', { key: 'Enter' });
            sheetActionInput.dispatchEvent(event);

            expect(window.submitAction).toHaveBeenCalled();
        });
    });

    describe('begin button delegation', () => {
        beforeEach(() => {
            document.body.innerHTML = '<div id="story"><button id="begin-btn">Begin</button></div>';
            window.DOMElements = {
                storyBox: document.getElementById('story')
            };
        });

        it('should call startNewAdventure when begin button is clicked', () => {
            init();
            const beginBtn = document.getElementById('begin-btn');
            beginBtn.click();

            expect(window.startNewAdventure).toHaveBeenCalledWith(true);
        });

        it('should call startNewAdventure when child of begin button is clicked', () => {
            document.body.innerHTML = '<div id="story"><button id="begin-btn"><span>Begin</span></button></div>';
            window.DOMElements = {
                storyBox: document.getElementById('story')
            };

            init();
            const span = document.querySelector('#begin-btn span');
            span.click();

            expect(window.startNewAdventure).toHaveBeenCalledWith(true);
        });
    });

    describe('initReadingMode', () => {
        beforeEach(() => {
            document.body.innerHTML = '<button id="reading-toggle"></button>';
        });

        it('should return early if reading toggle element not found', () => {
            document.body.innerHTML = '';
            expect(() => initReadingMode()).not.toThrow();
        });

        it('should add reading-mode class if saved preference is true', () => {
            localStorage.getItem.mockReturnValue('true');
            initReadingMode();

            expect(document.body.classList.contains('reading-mode')).toBe(true);
        });

        it('should not add reading-mode class if saved preference is false', () => {
            localStorage.getItem.mockReturnValue('false');
            initReadingMode();

            expect(document.body.classList.contains('reading-mode')).toBe(false);
        });

        it('should toggle reading-mode class on click', () => {
            initReadingMode();
            const readingToggle = document.getElementById('reading-toggle');

            readingToggle.click();
            expect(document.body.classList.contains('reading-mode')).toBe(true);
            expect(localStorage.setItem).toHaveBeenCalledWith('readingMode', true);

            readingToggle.click();
            expect(document.body.classList.contains('reading-mode')).toBe(false);
            expect(localStorage.setItem).toHaveBeenCalledWith('readingMode', false);
        });
    });

    describe('autoInit', () => {
        it('should be exposed to window', () => {
            expect(window.initApp).toBe(init);
            expect(window.initReadingMode).toBe(initReadingMode);
        });
    });

    describe('graceful degradation', () => {
        it('should not throw if hapticFeedback is not available', () => {
            document.body.innerHTML = '<button id="submit-btn"></button>';
            window.DOMElements = {
                submitBtn: document.getElementById('submit-btn')
            };
            window.hapticFeedback = undefined;

            init();
            const submitBtn = document.getElementById('submit-btn');
            expect(() => submitBtn.click()).not.toThrow();
        });

        it('should not throw if submitAction is not available', () => {
            document.body.innerHTML = '<button id="submit-btn"></button>';
            window.DOMElements = {
                submitBtn: document.getElementById('submit-btn')
            };
            window.submitAction = undefined;

            init();
            const submitBtn = document.getElementById('submit-btn');
            expect(() => submitBtn.click()).not.toThrow();
        });
    });
});
