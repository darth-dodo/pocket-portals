/**
 * Tests for game-state.js
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
    GameState,
    DOMElements,
    AgentConfig,
    LoadingPhrases,
    initDOMElements,
    getRandomLoadingPhrase,
    resetState
} from '../game-state.js';

describe('GameState', () => {
    it('should have correct initial values', () => {
        expect(GameState.sessionId).toBe(null);
        expect(GameState.currentChoices).toEqual([]);
        expect(GameState.isLoading).toBe(false);
        expect(GameState.turnCount).toBe(1);
        expect(GameState.combatState).toBe(null);
        expect(GameState.isInCombat).toBe(false);
        expect(GameState.currentAgent).toBe('narrator');
        expect(GameState.SCROLL_THROTTLE_MS).toBe(100);
    });

    it('should be mutable', () => {
        GameState.sessionId = 'test-session';
        GameState.turnCount = 5;
        GameState.isInCombat = true;

        expect(GameState.sessionId).toBe('test-session');
        expect(GameState.turnCount).toBe(5);
        expect(GameState.isInCombat).toBe(true);

        // Reset for other tests
        resetState();
    });
});

describe('DOMElements', () => {
    it('should have all expected element properties initialized to null', () => {
        // Story elements
        expect(DOMElements.storyBox).toBe(null);
        expect(DOMElements.choicesSection).toBe(null);
        expect(DOMElements.choicesDiv).toBe(null);
        expect(DOMElements.actionInput).toBe(null);
        expect(DOMElements.submitBtn).toBe(null);
        expect(DOMElements.loadingDiv).toBe(null);
        expect(DOMElements.errorDiv).toBe(null);

        // Bottom sheet elements
        expect(DOMElements.bottomSheet).toBe(null);
        expect(DOMElements.bottomSheetOverlay).toBe(null);

        // Header elements
        expect(DOMElements.gameHeader).toBe(null);
        expect(DOMElements.turnCounter).toBe(null);

        // Combat elements
        expect(DOMElements.combatHud).toBe(null);
        expect(DOMElements.playerHpBar).toBe(null);
    });
});

describe('AgentConfig', () => {
    it('should have narrator configuration', () => {
        expect(AgentConfig.narrator).toBeDefined();
        expect(AgentConfig.narrator.label).toBe('Narrator');
        expect(AgentConfig.narrator.icon).toBe('ra-scroll-unfurled');
        expect(AgentConfig.narrator.typingSpeed.base).toBe(30);
        expect(AgentConfig.narrator.typingSpeed.variance).toBe(15);
    });

    it('should have keeper configuration', () => {
        expect(AgentConfig.keeper).toBeDefined();
        expect(AgentConfig.keeper.label).toBe('Keeper');
        expect(AgentConfig.keeper.icon).toBe('ra-dice');
        expect(AgentConfig.keeper.typingSpeed.base).toBe(15);
    });

    it('should have jester configuration', () => {
        expect(AgentConfig.jester).toBeDefined();
        expect(AgentConfig.jester.label).toBe('Jester');
        expect(AgentConfig.jester.icon).toBe('ra-mask');
        expect(AgentConfig.jester.typingSpeed.variance).toBe(20);
    });

    it('should have player configuration', () => {
        expect(AgentConfig.player).toBeDefined();
        expect(AgentConfig.player.label).toBe('You');
        expect(AgentConfig.player.icon).toBe('ra-player');
    });
});

describe('LoadingPhrases', () => {
    it('should be an array with multiple phrases', () => {
        expect(Array.isArray(LoadingPhrases)).toBe(true);
        expect(LoadingPhrases.length).toBeGreaterThan(5);
    });

    it('should contain themed phrases', () => {
        expect(LoadingPhrases).toContain('Rolling for initiative...');
        expect(LoadingPhrases).toContain('The dice are tumbling...');
        expect(LoadingPhrases).toContain('Gathering mana...');
    });
});

describe('getRandomLoadingPhrase', () => {
    it('should return a string from LoadingPhrases', () => {
        const phrase = getRandomLoadingPhrase();

        expect(typeof phrase).toBe('string');
        expect(LoadingPhrases).toContain(phrase);
    });

    it('should return different phrases over multiple calls', () => {
        const phrases = new Set();
        // Call 50 times to get variety
        for (let i = 0; i < 50; i++) {
            phrases.add(getRandomLoadingPhrase());
        }
        // Should have gotten at least 3 different phrases
        expect(phrases.size).toBeGreaterThan(2);
    });
});

describe('resetState', () => {
    beforeEach(() => {
        // Modify state first
        GameState.sessionId = 'test-session';
        GameState.currentChoices = ['choice1', 'choice2'];
        GameState.isLoading = true;
        GameState.turnCount = 10;
        GameState.combatState = { hp: 100 };
        GameState.isInCombat = true;
        GameState.streamingContent = 'some content';
        GameState.currentAgent = 'keeper';
    });

    it('should reset all state values to defaults', () => {
        resetState();

        expect(GameState.sessionId).toBe(null);
        expect(GameState.currentChoices).toEqual([]);
        expect(GameState.isLoading).toBe(false);
        expect(GameState.turnCount).toBe(1);
        expect(GameState.combatState).toBe(null);
        expect(GameState.isInCombat).toBe(false);
        expect(GameState.streamingContent).toBe('');
        expect(GameState.currentAgent).toBe('narrator');
    });

    it('should reset streaming elements to null', () => {
        GameState.streamingMessageEl = document.createElement('div');
        GameState.streamingTextEl = document.createElement('span');

        resetState();

        expect(GameState.streamingMessageEl).toBe(null);
        expect(GameState.streamingTextEl).toBe(null);
    });
});

describe('initDOMElements', () => {
    beforeEach(() => {
        // Create mock DOM elements
        document.body.innerHTML = `
            <div id="story"></div>
            <div id="choices-section"></div>
            <div id="choices"></div>
            <input id="action-input" />
            <button id="submit-btn"></button>
            <div id="loading"></div>
            <div id="error"></div>
            <div id="session-display"></div>
            <button id="new-game-btn"></button>
            <div id="response-indicator"></div>
            <div id="bottom-sheet"></div>
            <div id="bottom-sheet-overlay"></div>
            <div id="bottom-sheet-handle"></div>
            <div id="bottom-sheet-content"></div>
            <div id="sheet-choices"></div>
            <input id="sheet-action-input" />
            <button id="sheet-submit-btn"></button>
            <div id="game-header"></div>
            <div id="turn-counter"></div>
            <div id="quest-title"></div>
            <div id="quest-subtitle"></div>
            <div id="progress-fill"></div>
            <div id="combat-hud"></div>
            <div id="turn-order-list"></div>
            <div id="player-hp-bar"></div>
            <div id="player-hp-text"></div>
            <div id="enemy-name-label"></div>
            <div id="enemy-hp-bar"></div>
            <div id="enemy-hp-text"></div>
            <div id="dice-display"></div>
            <div id="dice-result-text"></div>
        `;
    });

    it('should initialize story elements', () => {
        initDOMElements();

        expect(DOMElements.storyBox).toBe(document.getElementById('story'));
        expect(DOMElements.choicesSection).toBe(document.getElementById('choices-section'));
        expect(DOMElements.choicesDiv).toBe(document.getElementById('choices'));
        expect(DOMElements.actionInput).toBe(document.getElementById('action-input'));
        expect(DOMElements.submitBtn).toBe(document.getElementById('submit-btn'));
    });

    it('should initialize bottom sheet elements', () => {
        initDOMElements();

        expect(DOMElements.bottomSheet).toBe(document.getElementById('bottom-sheet'));
        expect(DOMElements.bottomSheetOverlay).toBe(document.getElementById('bottom-sheet-overlay'));
        expect(DOMElements.bottomSheetHandle).toBe(document.getElementById('bottom-sheet-handle'));
        expect(DOMElements.sheetChoices).toBe(document.getElementById('sheet-choices'));
    });

    it('should initialize header elements', () => {
        initDOMElements();

        expect(DOMElements.gameHeader).toBe(document.getElementById('game-header'));
        expect(DOMElements.turnCounter).toBe(document.getElementById('turn-counter'));
        expect(DOMElements.questTitle).toBe(document.getElementById('quest-title'));
        expect(DOMElements.progressFill).toBe(document.getElementById('progress-fill'));
    });

    it('should initialize combat elements', () => {
        initDOMElements();

        expect(DOMElements.combatHud).toBe(document.getElementById('combat-hud'));
        expect(DOMElements.playerHpBar).toBe(document.getElementById('player-hp-bar'));
        expect(DOMElements.enemyHpBar).toBe(document.getElementById('enemy-hp-bar'));
        expect(DOMElements.diceDisplay).toBe(document.getElementById('dice-display'));
    });
});
