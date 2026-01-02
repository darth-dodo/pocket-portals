/**
 * Tests for controllers.js - UI Controllers
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    BottomSheet,
    GameHeader,
    ResponseIndicator
} from '../controllers.js';

// Helper to create mock DOM elements
function createMockDOMElements() {
    return {
        bottomSheet: createMockElement('bottom-sheet'),
        bottomSheetOverlay: createMockElement('bottom-sheet-overlay'),
        bottomSheetHandle: createMockElement('bottom-sheet-handle'),
        sheetChoices: createMockElement('sheet-choices'),
        gameHeader: createMockElement('game-header'),
        turnCounter: createMockElement('turn-counter'),
        progressFill: createMockElement('progress-fill'),
        questTitle: createMockElement('quest-title'),
        questSubtitle: createMockElement('quest-subtitle'),
        responseIndicator: createMockResponseIndicator()
    };
}

function createMockElement(id) {
    const el = document.createElement('div');
    el.id = id;
    el.style = {};
    return el;
}

function createMockResponseIndicator() {
    const el = document.createElement('div');
    el.className = 'response-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'agent-avatar';
    el.appendChild(avatar);

    const name = document.createElement('div');
    name.className = 'agent-name';
    el.appendChild(name);

    return el;
}

describe('UI Controllers', () => {
    let mockDOMElements;
    let mockGameState;
    let mockAgentConfig;

    beforeEach(() => {
        // Setup mock DOM elements
        mockDOMElements = createMockDOMElements();
        window.DOMElements = mockDOMElements;

        // Setup mock GameState
        mockGameState = {
            turnCount: 1
        };
        window.GameState = mockGameState;

        // Setup mock AgentConfig
        mockAgentConfig = {
            narrator: { label: 'Narrator', icon: 'ra-scroll-unfurled' },
            keeper: { label: 'Keeper', icon: 'ra-key' },
            jester: { label: 'Jester', icon: 'ra-jester-hat' },
            player: { label: 'You', icon: 'ra-player' }
        };
        window.AgentConfig = mockAgentConfig;

        // Reset controller states
        BottomSheet.reset();
        GameHeader.reset();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('BottomSheet', () => {
        describe('initial state', () => {
            it('should have correct initial values', () => {
                expect(BottomSheet.isExpanded).toBe(false);
                expect(BottomSheet.startY).toBe(0);
                expect(BottomSheet.currentY).toBe(0);
                expect(BottomSheet.isDragging).toBe(false);
            });
        });

        describe('init', () => {
            it('should warn if required DOM elements are missing', () => {
                const warnSpy = vi.spyOn(console, 'warn');
                window.DOMElements = { bottomSheetHandle: null, bottomSheetOverlay: null };

                BottomSheet.init();

                expect(warnSpy).toHaveBeenCalledWith('BottomSheet: Required DOM elements not found');
            });

            it('should add event listeners when elements exist', () => {
                const addEventSpy = vi.spyOn(mockDOMElements.bottomSheetHandle, 'addEventListener');

                BottomSheet.init();

                expect(addEventSpy).toHaveBeenCalledWith('touchstart', expect.any(Function), { passive: true });
                expect(addEventSpy).toHaveBeenCalledWith('click', expect.any(Function));
            });
        });

        describe('expand', () => {
            it('should set isExpanded to true', () => {
                BottomSheet.expand();
                expect(BottomSheet.isExpanded).toBe(true);
            });

            it('should add expanded class and remove hidden class', () => {
                BottomSheet.expand();

                expect(mockDOMElements.bottomSheet.classList.contains('expanded')).toBe(true);
                expect(mockDOMElements.bottomSheet.classList.contains('hidden')).toBe(false);
            });

            it('should show overlay', () => {
                BottomSheet.expand();

                expect(mockDOMElements.bottomSheetOverlay.classList.contains('visible')).toBe(true);
            });

            it('should clear transform style', () => {
                mockDOMElements.bottomSheet.style.transform = 'translateY(100px)';

                BottomSheet.expand();

                expect(mockDOMElements.bottomSheet.style.transform).toBe('');
            });
        });

        describe('collapse', () => {
            it('should set isExpanded to false', () => {
                BottomSheet.isExpanded = true;
                BottomSheet.collapse();
                expect(BottomSheet.isExpanded).toBe(false);
            });

            it('should remove expanded class', () => {
                mockDOMElements.bottomSheet.classList.add('expanded');

                BottomSheet.collapse();

                expect(mockDOMElements.bottomSheet.classList.contains('expanded')).toBe(false);
            });

            it('should hide overlay', () => {
                mockDOMElements.bottomSheetOverlay.classList.add('visible');

                BottomSheet.collapse();

                expect(mockDOMElements.bottomSheetOverlay.classList.contains('visible')).toBe(false);
            });
        });

        describe('toggle', () => {
            it('should expand when collapsed', () => {
                BottomSheet.isExpanded = false;
                BottomSheet.toggle();
                expect(BottomSheet.isExpanded).toBe(true);
            });

            it('should collapse when expanded', () => {
                BottomSheet.isExpanded = true;
                BottomSheet.toggle();
                expect(BottomSheet.isExpanded).toBe(false);
            });
        });

        describe('hide', () => {
            it('should add hidden class', () => {
                BottomSheet.hide();
                expect(mockDOMElements.bottomSheet.classList.contains('hidden')).toBe(true);
            });

            it('should remove expanded class', () => {
                mockDOMElements.bottomSheet.classList.add('expanded');
                BottomSheet.hide();
                expect(mockDOMElements.bottomSheet.classList.contains('expanded')).toBe(false);
            });

            it('should set isExpanded to false', () => {
                BottomSheet.isExpanded = true;
                BottomSheet.hide();
                expect(BottomSheet.isExpanded).toBe(false);
            });

            it('should hide overlay', () => {
                mockDOMElements.bottomSheetOverlay.classList.add('visible');
                BottomSheet.hide();
                expect(mockDOMElements.bottomSheetOverlay.classList.contains('visible')).toBe(false);
            });
        });

        describe('show', () => {
            it('should remove hidden class', () => {
                mockDOMElements.bottomSheet.classList.add('hidden');
                BottomSheet.show();
                expect(mockDOMElements.bottomSheet.classList.contains('hidden')).toBe(false);
            });
        });

        describe('updateChoices', () => {
            it('should do nothing if sheetChoices is missing', () => {
                window.DOMElements.sheetChoices = null;
                expect(() => BottomSheet.updateChoices(['Choice 1'])).not.toThrow();
            });

            it('should clear existing choices', () => {
                mockDOMElements.sheetChoices.innerHTML = '<button>Old Choice</button>';

                BottomSheet.updateChoices(['New Choice']);

                expect(mockDOMElements.sheetChoices.innerHTML).not.toContain('Old Choice');
            });

            it('should create buttons for each choice', () => {
                BottomSheet.updateChoices(['Attack', 'Defend', 'Run']);

                const buttons = mockDOMElements.sheetChoices.querySelectorAll('button');
                expect(buttons.length).toBe(3);
            });

            it('should use correct icons for choices', () => {
                BottomSheet.updateChoices(['Attack', 'Talk', 'Walk']);

                const buttons = mockDOMElements.sheetChoices.querySelectorAll('button');
                expect(buttons[0].innerHTML).toContain('ra-axe');
                expect(buttons[1].innerHTML).toContain('ra-speech-bubble');
                expect(buttons[2].innerHTML).toContain('ra-boot-stomp');
            });

            it('should use default icon for choices beyond the icon list', () => {
                BottomSheet.updateChoices(['A', 'B', 'C', 'D']);

                const buttons = mockDOMElements.sheetChoices.querySelectorAll('button');
                expect(buttons[3].innerHTML).toContain('ra-hand');
            });

            it('should display choice text', () => {
                BottomSheet.updateChoices(['Cast Spell']);

                const button = mockDOMElements.sheetChoices.querySelector('button');
                expect(button.innerHTML).toContain('Cast Spell');
            });

            it('should show bottom sheet when choices are provided', () => {
                mockDOMElements.bottomSheet.classList.add('hidden');

                BottomSheet.updateChoices(['Choice']);

                expect(mockDOMElements.bottomSheet.classList.contains('hidden')).toBe(false);
            });

            it('should hide bottom sheet when no choices are provided', () => {
                BottomSheet.updateChoices([]);

                expect(mockDOMElements.bottomSheet.classList.contains('hidden')).toBe(true);
            });

            it('should trigger haptic feedback when choice button is clicked', () => {
                window.hapticFeedback = vi.fn();
                window.selectChoice = vi.fn();

                BottomSheet.updateChoices(['Choice 1']);

                const button = mockDOMElements.sheetChoices.querySelector('button');
                button.onclick();

                expect(window.hapticFeedback).toHaveBeenCalledWith('light');
            });

            it('should call selectChoice with correct index when clicked', () => {
                window.hapticFeedback = vi.fn();
                window.selectChoice = vi.fn();

                BottomSheet.updateChoices(['First', 'Second', 'Third']);

                const buttons = mockDOMElements.sheetChoices.querySelectorAll('button');
                buttons[1].onclick();

                expect(window.selectChoice).toHaveBeenCalledWith(2);
            });

            it('should collapse bottom sheet when choice is clicked', () => {
                window.hapticFeedback = vi.fn();
                window.selectChoice = vi.fn();
                BottomSheet.isExpanded = true;

                BottomSheet.updateChoices(['Choice']);
                const button = mockDOMElements.sheetChoices.querySelector('button');
                button.onclick();

                expect(BottomSheet.isExpanded).toBe(false);
            });
        });

        describe('onTouchStart', () => {
            it('should set isDragging to true', () => {
                const event = { touches: [{ clientY: 100 }] };

                BottomSheet.onTouchStart(event);

                expect(BottomSheet.isDragging).toBe(true);
            });

            it('should record startY from touch event', () => {
                const event = { touches: [{ clientY: 250 }] };

                BottomSheet.onTouchStart(event);

                expect(BottomSheet.startY).toBe(250);
            });

            it('should disable transitions on bottom sheet', () => {
                const event = { touches: [{ clientY: 100 }] };

                BottomSheet.onTouchStart(event);

                expect(mockDOMElements.bottomSheet.style.transition).toBe('none');
            });
        });

        describe('onTouchMove', () => {
            it('should do nothing if not dragging', () => {
                BottomSheet.isDragging = false;
                const event = { touches: [{ clientY: 100 }] };

                BottomSheet.onTouchMove(event);

                expect(BottomSheet.currentY).toBe(0);
            });

            it('should update currentY when dragging', () => {
                BottomSheet.isDragging = true;
                const event = { touches: [{ clientY: 150 }] };

                BottomSheet.onTouchMove(event);

                expect(BottomSheet.currentY).toBe(150);
            });
        });

        describe('onTouchEnd', () => {
            it('should do nothing if not dragging', () => {
                BottomSheet.isDragging = false;
                const initialState = BottomSheet.isExpanded;

                BottomSheet.onTouchEnd();

                expect(BottomSheet.isExpanded).toBe(initialState);
            });

            it('should set isDragging to false', () => {
                BottomSheet.isDragging = true;
                BottomSheet.startY = 200;
                BottomSheet.currentY = 200;

                BottomSheet.onTouchEnd();

                expect(BottomSheet.isDragging).toBe(false);
            });

            it('should trigger haptic feedback', () => {
                window.hapticFeedback = vi.fn();
                BottomSheet.isDragging = true;
                BottomSheet.startY = 200;
                BottomSheet.currentY = 200;

                BottomSheet.onTouchEnd();

                expect(window.hapticFeedback).toHaveBeenCalledWith('snap');
            });

            it('should collapse when expanded and dragged down past threshold', () => {
                BottomSheet.isDragging = true;
                BottomSheet.isExpanded = true;
                BottomSheet.startY = 100;
                BottomSheet.currentY = 200; // diff = -100

                BottomSheet.onTouchEnd();

                expect(BottomSheet.isExpanded).toBe(false);
            });

            it('should expand when collapsed and dragged up past threshold', () => {
                BottomSheet.isDragging = true;
                BottomSheet.isExpanded = false;
                BottomSheet.startY = 200;
                BottomSheet.currentY = 100; // diff = 100

                BottomSheet.onTouchEnd();

                expect(BottomSheet.isExpanded).toBe(true);
            });

            it('should snap back when drag does not exceed threshold', () => {
                BottomSheet.isDragging = true;
                BottomSheet.isExpanded = false;
                BottomSheet.startY = 200;
                BottomSheet.currentY = 180; // diff = 20, below threshold of 50

                BottomSheet.onTouchEnd();

                expect(BottomSheet.isExpanded).toBe(false);
            });
        });

        describe('reset', () => {
            it('should reset all state values', () => {
                BottomSheet.isExpanded = true;
                BottomSheet.startY = 100;
                BottomSheet.currentY = 200;
                BottomSheet.isDragging = true;

                BottomSheet.reset();

                expect(BottomSheet.isExpanded).toBe(false);
                expect(BottomSheet.startY).toBe(0);
                expect(BottomSheet.currentY).toBe(0);
                expect(BottomSheet.isDragging).toBe(false);
            });
        });
    });

    describe('GameHeader', () => {
        describe('initial state', () => {
            it('should have correct initial values', () => {
                expect(GameHeader.lastScrollY).toBe(0);
                expect(GameHeader.currentMilestone).toBe(0);
            });

            it('should have milestone names', () => {
                expect(GameHeader.milestones).toEqual(['start', 'explore', 'challenge', 'climax', 'resolution']);
            });
        });

        describe('init', () => {
            it('should add scroll event listener', () => {
                const addEventSpy = vi.spyOn(window, 'addEventListener');

                GameHeader.init();

                expect(addEventSpy).toHaveBeenCalledWith('scroll', expect.any(Function), { passive: true });
            });
        });

        describe('onScroll', () => {
            it('should do nothing if gameHeader is missing', () => {
                window.DOMElements.gameHeader = null;
                expect(() => GameHeader.onScroll()).not.toThrow();
            });

            it('should add scrolled class when scrolled past threshold', () => {
                Object.defineProperty(window, 'scrollY', { value: 50, writable: true });

                GameHeader.onScroll();

                expect(mockDOMElements.gameHeader.classList.contains('scrolled')).toBe(true);
            });

            it('should remove scrolled class when at top', () => {
                mockDOMElements.gameHeader.classList.add('scrolled');
                Object.defineProperty(window, 'scrollY', { value: 5, writable: true });

                GameHeader.onScroll();

                expect(mockDOMElements.gameHeader.classList.contains('scrolled')).toBe(false);
            });

            it('should update lastScrollY', () => {
                Object.defineProperty(window, 'scrollY', { value: 123, writable: true });

                GameHeader.onScroll();

                expect(GameHeader.lastScrollY).toBe(123);
            });
        });

        describe('updateTurn', () => {
            it('should update GameState turnCount', () => {
                GameHeader.updateTurn(5);
                expect(window.GameState.turnCount).toBe(5);
            });

            it('should update turn counter text content', () => {
                GameHeader.updateTurn(7);
                expect(mockDOMElements.turnCounter.textContent).toBe('7');
            });

            it('should handle missing turnCounter gracefully', () => {
                window.DOMElements.turnCounter = null;
                expect(() => GameHeader.updateTurn(5)).not.toThrow();
            });

            it('should update progress fill width based on turn count', () => {
                GameHeader.updateTurn(10);
                expect(mockDOMElements.progressFill.style.width).toBe('50%');
            });

            it('should cap progress at 100%', () => {
                GameHeader.updateTurn(25);
                expect(mockDOMElements.progressFill.style.width).toBe('100%');
            });

            it('should handle missing progressFill gracefully', () => {
                window.DOMElements.progressFill = null;
                expect(() => GameHeader.updateTurn(5)).not.toThrow();
            });

            it('should update milestones based on turn count', () => {
                const setMilestoneSpy = vi.spyOn(GameHeader, 'setMilestone');

                GameHeader.updateTurn(12);

                expect(setMilestoneSpy).toHaveBeenCalledWith(2);
            });

            it('should cap milestone index to maximum', () => {
                const setMilestoneSpy = vi.spyOn(GameHeader, 'setMilestone');

                GameHeader.updateTurn(100);

                expect(setMilestoneSpy).toHaveBeenCalledWith(4);
            });
        });

        describe('setMilestone', () => {
            let milestoneEls;

            beforeEach(() => {
                // Create milestone elements in the document
                document.body.innerHTML = `
                    <div class="milestone"></div>
                    <div class="milestone"></div>
                    <div class="milestone"></div>
                    <div class="milestone"></div>
                    <div class="milestone"></div>
                `;
                milestoneEls = document.querySelectorAll('.milestone');
            });

            afterEach(() => {
                document.body.innerHTML = '';
            });

            it('should update currentMilestone', () => {
                GameHeader.setMilestone(2);
                expect(GameHeader.currentMilestone).toBe(2);
            });

            it('should add reached class to milestones before current', () => {
                GameHeader.setMilestone(3);

                expect(milestoneEls[0].classList.contains('reached')).toBe(true);
                expect(milestoneEls[1].classList.contains('reached')).toBe(true);
                expect(milestoneEls[2].classList.contains('reached')).toBe(true);
            });

            it('should add current class to current milestone', () => {
                GameHeader.setMilestone(2);

                expect(milestoneEls[2].classList.contains('current')).toBe(true);
            });

            it('should remove all classes when index is 0', () => {
                milestoneEls[0].classList.add('reached');
                milestoneEls[1].classList.add('current');

                GameHeader.setMilestone(0);

                expect(milestoneEls[0].classList.contains('current')).toBe(true);
                expect(milestoneEls[0].classList.contains('reached')).toBe(false);
                expect(milestoneEls[1].classList.contains('current')).toBe(false);
            });
        });

        describe('setQuestTitle', () => {
            it('should set quest title text', () => {
                GameHeader.setQuestTitle('The Dark Forest');
                expect(mockDOMElements.questTitle.textContent).toBe('The Dark Forest');
            });

            it('should use default title when null is passed', () => {
                GameHeader.setQuestTitle(null);
                expect(mockDOMElements.questTitle.textContent).toBe('Pocket Portals');
            });

            it('should set subtitle when provided', () => {
                GameHeader.setQuestTitle('Main Quest', 'Chapter 1');
                expect(mockDOMElements.questSubtitle.textContent).toBe('Chapter 1');
            });

            it('should not set subtitle when null', () => {
                mockDOMElements.questSubtitle.textContent = 'Existing';
                GameHeader.setQuestTitle('Title', null);
                expect(mockDOMElements.questSubtitle.textContent).toBe('Existing');
            });

            it('should handle missing questTitle gracefully', () => {
                window.DOMElements.questTitle = null;
                expect(() => GameHeader.setQuestTitle('Test')).not.toThrow();
            });

            it('should handle missing questSubtitle gracefully', () => {
                window.DOMElements.questSubtitle = null;
                expect(() => GameHeader.setQuestTitle('Test', 'Subtitle')).not.toThrow();
            });
        });

        describe('reset', () => {
            it('should reset all state values', () => {
                GameHeader.lastScrollY = 500;
                GameHeader.currentMilestone = 3;

                GameHeader.reset();

                expect(GameHeader.lastScrollY).toBe(0);
                expect(GameHeader.currentMilestone).toBe(0);
            });
        });
    });

    describe('ResponseIndicator', () => {
        describe('show', () => {
            it('should do nothing if responseIndicator is missing', () => {
                window.DOMElements.responseIndicator = null;
                expect(() => ResponseIndicator.show('narrator')).not.toThrow();
            });

            it('should set correct class for agent type', () => {
                ResponseIndicator.show('narrator');
                expect(mockDOMElements.responseIndicator.className).toBe('response-indicator visible agent-narrator');
            });

            it('should set correct class for different agent types', () => {
                ResponseIndicator.show('keeper');
                expect(mockDOMElements.responseIndicator.className).toContain('agent-keeper');
            });

            it('should update avatar icon', () => {
                ResponseIndicator.show('narrator');

                const avatar = mockDOMElements.responseIndicator.querySelector('.agent-avatar');
                expect(avatar.innerHTML).toContain('ra-scroll-unfurled');
            });

            it('should update agent name', () => {
                ResponseIndicator.show('narrator');

                const name = mockDOMElements.responseIndicator.querySelector('.agent-name');
                expect(name.textContent).toBe('Narrator');
            });

            it('should fallback to narrator config for unknown agent type', () => {
                ResponseIndicator.show('unknown');

                const name = mockDOMElements.responseIndicator.querySelector('.agent-name');
                expect(name.textContent).toBe('Narrator');
            });

            it('should handle missing avatar element gracefully', () => {
                mockDOMElements.responseIndicator.innerHTML = '<div class="agent-name"></div>';
                expect(() => ResponseIndicator.show('narrator')).not.toThrow();
            });

            it('should handle missing name element gracefully', () => {
                mockDOMElements.responseIndicator.innerHTML = '<div class="agent-avatar"></div>';
                expect(() => ResponseIndicator.show('narrator')).not.toThrow();
            });
        });

        describe('hide', () => {
            it('should do nothing if responseIndicator is missing', () => {
                window.DOMElements.responseIndicator = null;
                expect(() => ResponseIndicator.hide()).not.toThrow();
            });

            it('should remove visible class', () => {
                mockDOMElements.responseIndicator.classList.add('visible');

                ResponseIndicator.hide();

                expect(mockDOMElements.responseIndicator.classList.contains('visible')).toBe(false);
            });
        });
    });

    describe('window exports', () => {
        it('should expose BottomSheet to window', () => {
            expect(window.BottomSheet).toBe(BottomSheet);
        });

        it('should expose GameHeader to window', () => {
            expect(window.GameHeader).toBe(GameHeader);
        });

        it('should expose ResponseIndicator to window', () => {
            expect(window.ResponseIndicator).toBe(ResponseIndicator);
        });
    });
});
