/**
 * Tests for messages.js - Message Display and Streaming
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    formatMessageText,
    createMessageElement,
    removeWelcomeIfPresent,
    addMessage,
    startStreamingMessage,
    appendStreamingChar,
    endStreamingMessage,
    createChoiceButton,
    getChoiceIcon,
    updateChoices,
    setLoading,
    showError
} from '../messages.js';

describe('Message Functions', () => {
    // Mock DOM and window state before each test
    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = `
            <div id="story"></div>
            <div id="choices-section" class="hidden"></div>
            <div id="choices"></div>
            <input id="action-input" />
            <button id="submit-btn"></button>
            <div id="loading"></div>
            <div id="error"></div>
            <div id="loading-text"></div>
        `;

        // Setup window.DOMElements
        window.DOMElements = {
            storyBox: document.getElementById('story'),
            choicesSection: document.getElementById('choices-section'),
            choicesDiv: document.getElementById('choices'),
            actionInput: document.getElementById('action-input'),
            submitBtn: document.getElementById('submit-btn'),
            loadingDiv: document.getElementById('loading'),
            errorDiv: document.getElementById('error')
        };

        // Setup window.GameState
        window.GameState = {
            sessionId: null,
            currentChoices: [],
            isLoading: false,
            turnCount: 1,
            streamingMessageEl: null,
            streamingTextEl: null,
            streamingContent: '',
            currentAgent: 'narrator',
            lastScrollTime: 0,
            SCROLL_THROTTLE_MS: 100
        };

        // Setup window.AgentConfig
        window.AgentConfig = {
            narrator: { label: 'Narrator', icon: 'ra-scroll-unfurled' },
            keeper: { label: 'Keeper', icon: 'ra-key' },
            jester: { label: 'Jester', icon: 'ra-jester-hat' },
            player: { label: 'You', icon: 'ra-knight-helmet' }
        };

        // Mock optional window functions
        window.ResponseIndicator = {
            show: vi.fn(),
            hide: vi.fn()
        };
        window.GameHeader = {
            updateTurn: vi.fn()
        };
        window.BottomSheet = {
            updateChoices: vi.fn(),
            hide: vi.fn()
        };
        window.hapticFeedback = vi.fn();
        window.selectChoice = vi.fn();
        window.getRandomLoadingPhrase = vi.fn(() => 'Loading...');

        // Mock requestAnimationFrame
        vi.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
            cb();
            return 1;
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
        delete window.DOMElements;
        delete window.GameState;
        delete window.AgentConfig;
        delete window.ResponseIndicator;
        delete window.GameHeader;
        delete window.BottomSheet;
        delete window.hapticFeedback;
        delete window.selectChoice;
        delete window.getRandomLoadingPhrase;
    });

    describe('formatMessageText', () => {
        it('should replace double newlines with paragraph breaks', () => {
            const result = formatMessageText('Hello\n\nWorld');
            expect(result).toBe('Hello</p><p>World');
        });

        it('should replace single newlines with line breaks', () => {
            const result = formatMessageText('Hello\nWorld');
            expect(result).toBe('Hello<br>World');
        });

        it('should handle mixed newlines correctly', () => {
            const result = formatMessageText('Line1\nLine2\n\nParagraph2');
            expect(result).toBe('Line1<br>Line2</p><p>Paragraph2');
        });

        it('should handle text without newlines', () => {
            const result = formatMessageText('Simple text');
            expect(result).toBe('Simple text');
        });

        it('should handle empty string', () => {
            const result = formatMessageText('');
            expect(result).toBe('');
        });

        it('should handle multiple consecutive double newlines', () => {
            const result = formatMessageText('A\n\nB\n\nC');
            expect(result).toBe('A</p><p>B</p><p>C');
        });
    });

    describe('createMessageElement', () => {
        it('should create a div with correct class', () => {
            const config = { icon: 'ra-test', label: 'Test' };
            const element = createMessageElement('narrator', config, 'Hello');

            expect(element.tagName).toBe('DIV');
            expect(element.className).toBe('message message-narrator');
        });

        it('should include the message label with icon', () => {
            const config = { icon: 'ra-scroll', label: 'Narrator' };
            const element = createMessageElement('narrator', config, 'Content');

            const label = element.querySelector('.message-label');
            expect(label).not.toBeNull();
            expect(label.innerHTML).toContain('ra-scroll');
            expect(label.textContent).toContain('Narrator');
        });

        it('should include the message text content', () => {
            const config = { icon: 'ra-test', label: 'Test' };
            const element = createMessageElement('keeper', config, 'Test content');

            const textEl = element.querySelector('.message-text p');
            expect(textEl).not.toBeNull();
            expect(textEl.innerHTML).toBe('Test content');
        });

        it('should handle HTML content in text', () => {
            const config = { icon: 'ra-test', label: 'Test' };
            const element = createMessageElement('jester', config, 'Line1<br>Line2');

            const textEl = element.querySelector('.message-text p');
            expect(textEl.innerHTML).toBe('Line1<br>Line2');
        });
    });

    describe('removeWelcomeIfPresent', () => {
        it('should return false for null storyBox', () => {
            const result = removeWelcomeIfPresent(null);
            expect(result).toBe(false);
        });

        it('should return false when no welcome element exists', () => {
            const storyBox = document.getElementById('story');
            const result = removeWelcomeIfPresent(storyBox);
            expect(result).toBe(false);
        });

        it('should remove welcome element and return true when present', () => {
            const storyBox = document.getElementById('story');
            const welcome = document.createElement('div');
            welcome.className = 'welcome';
            storyBox.appendChild(welcome);

            const result = removeWelcomeIfPresent(storyBox);

            expect(result).toBe(true);
            expect(storyBox.querySelector('.welcome')).toBeNull();
        });
    });

    describe('addMessage', () => {
        it('should do nothing if storyBox is not available', () => {
            window.DOMElements.storyBox = null;
            addMessage('Test', 'narrator');
            // No error should be thrown
        });

        it('should add a message to the story box', () => {
            addMessage('Hello world', 'narrator');

            const storyBox = document.getElementById('story');
            const messages = storyBox.querySelectorAll('.message');
            expect(messages.length).toBe(1);
        });

        it('should apply correct class for message type', () => {
            addMessage('Test', 'keeper');

            const storyBox = document.getElementById('story');
            const message = storyBox.querySelector('.message-keeper');
            expect(message).not.toBeNull();
        });

        it('should format text with newlines', () => {
            addMessage('Line1\nLine2', 'narrator');

            const storyBox = document.getElementById('story');
            const textEl = storyBox.querySelector('.message-text p');
            expect(textEl.innerHTML).toBe('Line1<br>Line2');
        });

        it('should remove welcome element when adding message', () => {
            const storyBox = document.getElementById('story');
            const welcome = document.createElement('div');
            welcome.className = 'welcome';
            storyBox.appendChild(welcome);

            addMessage('Test', 'narrator');

            expect(storyBox.querySelector('.welcome')).toBeNull();
        });

        it('should scroll to bottom after adding message', () => {
            const storyBox = document.getElementById('story');
            Object.defineProperty(storyBox, 'scrollHeight', { value: 500, writable: true });

            addMessage('Test', 'narrator');

            expect(storyBox.scrollTop).toBe(500);
        });

        it('should use fallback config for unknown agent type', () => {
            addMessage('Test', 'unknown_agent');

            const storyBox = document.getElementById('story');
            const label = storyBox.querySelector('.message-label');
            expect(label.textContent).toContain('Narrator');
        });
    });

    describe('startStreamingMessage', () => {
        it('should do nothing if storyBox is not available', () => {
            window.DOMElements.storyBox = null;
            startStreamingMessage('narrator');
            expect(window.GameState.streamingMessageEl).toBeNull();
        });

        it('should set current agent in state', () => {
            startStreamingMessage('keeper');
            expect(window.GameState.currentAgent).toBe('keeper');
        });

        it('should show response indicator', () => {
            startStreamingMessage('narrator');
            expect(window.ResponseIndicator.show).toHaveBeenCalledWith('narrator');
        });

        it('should create streaming message element', () => {
            startStreamingMessage('jester');

            expect(window.GameState.streamingMessageEl).not.toBeNull();
            expect(window.GameState.streamingMessageEl.className).toBe('message message-jester');
        });

        it('should append message to story box', () => {
            startStreamingMessage('narrator');

            const storyBox = document.getElementById('story');
            expect(storyBox.querySelectorAll('.message').length).toBe(1);
        });

        it('should initialize streaming text element with streaming-text class', () => {
            startStreamingMessage('narrator');

            expect(window.GameState.streamingTextEl).not.toBeNull();
            expect(window.GameState.streamingTextEl.classList.contains('streaming-text')).toBe(true);
        });

        it('should initialize streaming content as empty', () => {
            window.GameState.streamingContent = 'previous';
            startStreamingMessage('narrator');
            expect(window.GameState.streamingContent).toBe('');
        });

        it('should remove welcome element when starting stream', () => {
            const storyBox = document.getElementById('story');
            const welcome = document.createElement('div');
            welcome.className = 'welcome';
            storyBox.appendChild(welcome);

            startStreamingMessage('narrator');

            expect(storyBox.querySelector('.welcome')).toBeNull();
        });
    });

    describe('appendStreamingChar', () => {
        beforeEach(() => {
            startStreamingMessage('narrator');
        });

        it('should do nothing if streamingTextEl is null', () => {
            window.GameState.streamingTextEl = null;
            appendStreamingChar('X');
            // No error should be thrown
        });

        it('should append character to streaming content', () => {
            appendStreamingChar('H');
            appendStreamingChar('i');

            expect(window.GameState.streamingContent).toBe('Hi');
        });

        it('should update streaming text element innerHTML', () => {
            appendStreamingChar('H');
            appendStreamingChar('i');

            expect(window.GameState.streamingTextEl.innerHTML).toBe('Hi');
        });

        it('should format newlines in streaming content', () => {
            'Hello\nWorld'.split('').forEach(c => appendStreamingChar(c));

            expect(window.GameState.streamingTextEl.innerHTML).toBe('Hello<br>World');
        });

        it('should throttle scroll updates based on SCROLL_THROTTLE_MS', () => {
            const storyBox = document.getElementById('story');
            Object.defineProperty(storyBox, 'scrollHeight', { value: 100, writable: true });

            // First char should scroll
            appendStreamingChar('A');
            expect(window.requestAnimationFrame).toHaveBeenCalled();

            // Reset mock count and set lastScrollTime to now
            vi.mocked(window.requestAnimationFrame).mockClear();
            window.GameState.lastScrollTime = Date.now();

            // Immediate second char should not trigger scroll due to throttle
            appendStreamingChar('B');
            expect(window.requestAnimationFrame).not.toHaveBeenCalled();
        });
    });

    describe('endStreamingMessage', () => {
        beforeEach(() => {
            startStreamingMessage('narrator');
            appendStreamingChar('T');
            appendStreamingChar('e');
            appendStreamingChar('s');
            appendStreamingChar('t');
        });

        it('should hide response indicator', () => {
            endStreamingMessage();
            expect(window.ResponseIndicator.hide).toHaveBeenCalled();
        });

        it('should remove streaming-text class from text element', () => {
            const textEl = window.GameState.streamingTextEl;
            expect(textEl.classList.contains('streaming-text')).toBe(true);

            endStreamingMessage();

            expect(textEl.classList.contains('streaming-text')).toBe(false);
        });

        it('should clear streaming state', () => {
            endStreamingMessage();

            expect(window.GameState.streamingMessageEl).toBeNull();
            expect(window.GameState.streamingTextEl).toBeNull();
            expect(window.GameState.streamingContent).toBe('');
        });

        it('should update turn counter via GameHeader', () => {
            window.GameState.turnCount = 5;
            endStreamingMessage();

            expect(window.GameHeader.updateTurn).toHaveBeenCalledWith(6);
        });

        it('should handle missing ResponseIndicator gracefully', () => {
            delete window.ResponseIndicator;
            expect(() => endStreamingMessage()).not.toThrow();
        });

        it('should handle missing GameHeader gracefully', () => {
            delete window.GameHeader;
            expect(() => endStreamingMessage()).not.toThrow();
        });

        it('should handle null streamingTextEl gracefully', () => {
            window.GameState.streamingTextEl = null;
            expect(() => endStreamingMessage()).not.toThrow();
        });
    });

    describe('getChoiceIcon', () => {
        it('should return ra-axe for index 0', () => {
            expect(getChoiceIcon(0)).toBe('ra-axe');
        });

        it('should return ra-speech-bubble for index 1', () => {
            expect(getChoiceIcon(1)).toBe('ra-speech-bubble');
        });

        it('should return ra-boot-stomp for index 2', () => {
            expect(getChoiceIcon(2)).toBe('ra-boot-stomp');
        });

        it('should return ra-hand for index beyond defined icons', () => {
            expect(getChoiceIcon(3)).toBe('ra-hand');
            expect(getChoiceIcon(10)).toBe('ra-hand');
        });
    });

    describe('createChoiceButton', () => {
        it('should create a button element', () => {
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            expect(btn.tagName).toBe('BUTTON');
        });

        it('should have correct class', () => {
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            expect(btn.className).toBe('nes-btn choice-btn');
        });

        it('should include icon in innerHTML', () => {
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            expect(btn.innerHTML).toContain('ra-axe');
        });

        it('should include choice text in innerHTML', () => {
            const btn = createChoiceButton('Attack the goblin', 0, 'ra-axe');
            expect(btn.innerHTML).toContain('Attack the goblin');
        });

        it('should trigger haptic feedback on click', () => {
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            btn.click();

            expect(window.hapticFeedback).toHaveBeenCalledWith('light');
        });

        it('should call selectChoice with 1-based index on click', () => {
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            btn.click();

            expect(window.selectChoice).toHaveBeenCalledWith(1);
        });

        it('should call selectChoice with correct index for non-zero index', () => {
            const btn = createChoiceButton('Run', 2, 'ra-boot-stomp');
            btn.click();

            expect(window.selectChoice).toHaveBeenCalledWith(3);
        });

        it('should handle missing hapticFeedback function', () => {
            delete window.hapticFeedback;
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            expect(() => btn.click()).not.toThrow();
        });

        it('should handle missing selectChoice function', () => {
            delete window.selectChoice;
            const btn = createChoiceButton('Attack', 0, 'ra-axe');
            expect(() => btn.click()).not.toThrow();
        });
    });

    describe('updateChoices', () => {
        it('should store choices in GameState', () => {
            const choices = ['Attack', 'Defend', 'Run'];
            updateChoices(choices);

            expect(window.GameState.currentChoices).toEqual(choices);
        });

        it('should handle null choices by setting empty array', () => {
            updateChoices(null);
            expect(window.GameState.currentChoices).toEqual([]);
        });

        it('should handle undefined choices by setting empty array', () => {
            updateChoices(undefined);
            expect(window.GameState.currentChoices).toEqual([]);
        });

        it('should show choices section when choices exist', () => {
            const choicesSection = document.getElementById('choices-section');
            choicesSection.classList.add('hidden');

            updateChoices(['Attack', 'Defend']);

            expect(choicesSection.classList.contains('hidden')).toBe(false);
        });

        it('should hide choices section when no choices', () => {
            const choicesSection = document.getElementById('choices-section');
            choicesSection.classList.remove('hidden');

            updateChoices([]);

            expect(choicesSection.classList.contains('hidden')).toBe(true);
        });

        it('should create choice buttons in choices div', () => {
            updateChoices(['Attack', 'Defend', 'Run']);

            const choicesDiv = document.getElementById('choices');
            const buttons = choicesDiv.querySelectorAll('.choice-btn');
            expect(buttons.length).toBe(3);
        });

        it('should clear previous choices before adding new ones', () => {
            updateChoices(['Attack']);
            updateChoices(['Defend', 'Run']);

            const choicesDiv = document.getElementById('choices');
            const buttons = choicesDiv.querySelectorAll('.choice-btn');
            expect(buttons.length).toBe(2);
        });

        it('should assign correct icons to choices', () => {
            updateChoices(['Attack', 'Talk', 'Run', 'Wait']);

            const choicesDiv = document.getElementById('choices');
            const buttons = choicesDiv.querySelectorAll('.choice-btn');

            expect(buttons[0].innerHTML).toContain('ra-axe');
            expect(buttons[1].innerHTML).toContain('ra-speech-bubble');
            expect(buttons[2].innerHTML).toContain('ra-boot-stomp');
            expect(buttons[3].innerHTML).toContain('ra-hand');
        });

        it('should update BottomSheet with choices', () => {
            const choices = ['Attack', 'Defend'];
            updateChoices(choices);

            expect(window.BottomSheet.updateChoices).toHaveBeenCalledWith(choices);
        });

        it('should handle missing BottomSheet gracefully', () => {
            delete window.BottomSheet;
            expect(() => updateChoices(['Attack'])).not.toThrow();
        });

        it('should handle missing DOM elements gracefully', () => {
            window.DOMElements.choicesSection = null;
            window.DOMElements.choicesDiv = null;

            expect(() => updateChoices(['Attack'])).not.toThrow();
        });
    });

    describe('setLoading', () => {
        it('should update isLoading state', () => {
            setLoading(true);
            expect(window.GameState.isLoading).toBe(true);

            setLoading(false);
            expect(window.GameState.isLoading).toBe(false);
        });

        it('should toggle visible class on loading div', () => {
            const loadingDiv = document.getElementById('loading');

            setLoading(true);
            expect(loadingDiv.classList.contains('visible')).toBe(true);

            setLoading(false);
            expect(loadingDiv.classList.contains('visible')).toBe(false);
        });

        it('should disable submit button when loading', () => {
            const submitBtn = document.getElementById('submit-btn');

            setLoading(true);
            expect(submitBtn.disabled).toBe(true);

            setLoading(false);
            expect(submitBtn.disabled).toBe(false);
        });

        it('should disable action input when loading', () => {
            const actionInput = document.getElementById('action-input');

            setLoading(true);
            expect(actionInput.disabled).toBe(true);

            setLoading(false);
            expect(actionInput.disabled).toBe(false);
        });

        it('should hide choices section when loading', () => {
            const choicesSection = document.getElementById('choices-section');
            choicesSection.classList.remove('hidden');

            setLoading(true);

            expect(choicesSection.classList.contains('hidden')).toBe(true);
        });

        it('should set random loading phrase when loading', () => {
            window.getRandomLoadingPhrase.mockReturnValue('Rolling dice...');
            const loadingText = document.getElementById('loading-text');

            setLoading(true);

            expect(loadingText.textContent).toBe('Rolling dice...');
        });

        it('should hide BottomSheet when loading', () => {
            setLoading(true);
            expect(window.BottomSheet.hide).toHaveBeenCalled();
        });

        it('should disable all choice buttons when loading', () => {
            // Add some choice buttons first
            updateChoices(['Attack', 'Defend']);

            setLoading(true);

            const buttons = document.querySelectorAll('.choice-btn');
            buttons.forEach(btn => {
                expect(btn.disabled).toBe(true);
            });
        });

        it('should enable choice buttons when not loading', () => {
            updateChoices(['Attack', 'Defend']);
            setLoading(true);
            setLoading(false);

            const buttons = document.querySelectorAll('.choice-btn');
            buttons.forEach(btn => {
                expect(btn.disabled).toBe(false);
            });
        });

        it('should handle missing BottomSheet gracefully', () => {
            delete window.BottomSheet;
            expect(() => setLoading(true)).not.toThrow();
        });

        it('should handle missing DOM elements gracefully', () => {
            window.DOMElements = {};
            expect(() => setLoading(true)).not.toThrow();
        });

        it('should handle missing getRandomLoadingPhrase gracefully', () => {
            delete window.getRandomLoadingPhrase;
            expect(() => setLoading(true)).not.toThrow();
        });
    });

    describe('showError', () => {
        it('should do nothing if errorDiv is not available', () => {
            window.DOMElements.errorDiv = null;
            expect(() => showError('Error!')).not.toThrow();
        });

        it('should set error message text', () => {
            showError('Something went wrong');

            const errorDiv = document.getElementById('error');
            expect(errorDiv.textContent).toBe('Something went wrong');
        });

        it('should add visible class to error div', () => {
            const errorDiv = document.getElementById('error');

            showError('Error!');

            expect(errorDiv.classList.contains('visible')).toBe(true);
        });

        it('should remove visible class after 5 seconds', () => {
            vi.useFakeTimers();

            const errorDiv = document.getElementById('error');
            showError('Error!');

            expect(errorDiv.classList.contains('visible')).toBe(true);

            vi.advanceTimersByTime(5000);

            expect(errorDiv.classList.contains('visible')).toBe(false);

            vi.useRealTimers();
        });

        it('should not remove visible class before 5 seconds', () => {
            vi.useFakeTimers();

            const errorDiv = document.getElementById('error');
            showError('Error!');

            vi.advanceTimersByTime(4999);

            expect(errorDiv.classList.contains('visible')).toBe(true);

            vi.useRealTimers();
        });
    });

    describe('window exports', () => {
        it('should expose all main functions to window', () => {
            expect(window.addMessage).toBe(addMessage);
            expect(window.startStreamingMessage).toBe(startStreamingMessage);
            expect(window.appendStreamingChar).toBe(appendStreamingChar);
            expect(window.endStreamingMessage).toBe(endStreamingMessage);
            expect(window.updateChoices).toBe(updateChoices);
            expect(window.setLoading).toBe(setLoading);
            expect(window.showError).toBe(showError);
        });

        it('should expose helper functions to window', () => {
            expect(window.formatMessageText).toBe(formatMessageText);
            expect(window.createMessageElement).toBe(createMessageElement);
            expect(window.removeWelcomeIfPresent).toBe(removeWelcomeIfPresent);
            expect(window.createChoiceButton).toBe(createChoiceButton);
            expect(window.getChoiceIcon).toBe(getChoiceIcon);
        });
    });
});
