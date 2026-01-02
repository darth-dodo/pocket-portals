/**
 * Tests for combat.js - Combat System
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    createInitialCombatState,
    findCombatantByType,
    findCombatantById,
    calculateHpPercentage,
    isPlayerTurn,
    getCurrentTurnCombatant,
    formatHpText,
    formatDiceRollText,
    showCombatHUD,
    hideCombatHUD,
    updateCombatHUD,
    showDiceRoll,
    executeCombatAction,
    startCombat
} from '../combat.js';

// Helper to create a mock combat state
function createMockCombatState(overrides = {}) {
    return {
        combatants: [
            { id: 'player-1', type: 'player', name: 'Hero', current_hp: 100, max_hp: 100 },
            { id: 'enemy-1', type: 'enemy', name: 'Goblin', current_hp: 30, max_hp: 30 }
        ],
        turn_order: ['player-1', 'enemy-1'],
        current_turn_index: 0,
        phase: 'player_turn',
        ...overrides
    };
}

// Setup mock window objects
function setupWindowMocks() {
    window.GameState = {
        sessionId: 'test-session-123',
        isInCombat: false,
        combatState: null
    };

    window.DOMElements = {
        combatHud: document.createElement('div'),
        actionInput: document.createElement('input'),
        submitBtn: document.createElement('button'),
        turnOrderList: document.createElement('ul'),
        playerHpBar: document.createElement('progress'),
        playerHpText: document.createElement('span'),
        enemyNameLabel: document.createElement('span'),
        enemyHpBar: document.createElement('progress'),
        enemyHpText: document.createElement('span'),
        diceDisplay: document.createElement('div'),
        diceResultText: document.createElement('span')
    };

    // Add a dice icon to the dice display
    const diceIcon = document.createElement('i');
    diceIcon.className = 'dice-icon';
    window.DOMElements.diceDisplay.appendChild(diceIcon);

    window.addMessage = vi.fn();
    window.showError = vi.fn();
    window.hapticFeedback = vi.fn();
}

describe('Combat System', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        setupWindowMocks();
        document.body.innerHTML = '<div class="combat-actions"><button>Attack</button><button>Defend</button></div>';
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    describe('createInitialCombatState', () => {
        it('should return an object with empty combatants array', () => {
            const state = createInitialCombatState();
            expect(state.combatants).toEqual([]);
        });

        it('should return an object with empty turn_order array', () => {
            const state = createInitialCombatState();
            expect(state.turn_order).toEqual([]);
        });

        it('should return an object with current_turn_index of 0', () => {
            const state = createInitialCombatState();
            expect(state.current_turn_index).toBe(0);
        });

        it('should return an object with phase set to setup', () => {
            const state = createInitialCombatState();
            expect(state.phase).toBe('setup');
        });

        it('should return a new object each time', () => {
            const state1 = createInitialCombatState();
            const state2 = createInitialCombatState();
            expect(state1).not.toBe(state2);
        });
    });

    describe('findCombatantByType', () => {
        it('should find player combatant', () => {
            const state = createMockCombatState();
            const player = findCombatantByType(state, 'player');
            expect(player).toBeDefined();
            expect(player.id).toBe('player-1');
            expect(player.name).toBe('Hero');
        });

        it('should find enemy combatant', () => {
            const state = createMockCombatState();
            const enemy = findCombatantByType(state, 'enemy');
            expect(enemy).toBeDefined();
            expect(enemy.id).toBe('enemy-1');
            expect(enemy.name).toBe('Goblin');
        });

        it('should return undefined for non-existent type', () => {
            const state = createMockCombatState();
            const result = findCombatantByType(state, 'npc');
            expect(result).toBeUndefined();
        });

        it('should return undefined for null state', () => {
            const result = findCombatantByType(null, 'player');
            expect(result).toBeUndefined();
        });

        it('should return undefined for undefined state', () => {
            const result = findCombatantByType(undefined, 'player');
            expect(result).toBeUndefined();
        });

        it('should return undefined for state without combatants', () => {
            const result = findCombatantByType({}, 'player');
            expect(result).toBeUndefined();
        });

        it('should return undefined for state with non-array combatants', () => {
            const result = findCombatantByType({ combatants: 'invalid' }, 'player');
            expect(result).toBeUndefined();
        });
    });

    describe('findCombatantById', () => {
        it('should find combatant by ID', () => {
            const state = createMockCombatState();
            const combatant = findCombatantById(state, 'player-1');
            expect(combatant).toBeDefined();
            expect(combatant.name).toBe('Hero');
        });

        it('should return undefined for non-existent ID', () => {
            const state = createMockCombatState();
            const result = findCombatantById(state, 'non-existent');
            expect(result).toBeUndefined();
        });

        it('should return undefined for null state', () => {
            const result = findCombatantById(null, 'player-1');
            expect(result).toBeUndefined();
        });

        it('should return undefined for state without combatants array', () => {
            const result = findCombatantById({ combatants: null }, 'player-1');
            expect(result).toBeUndefined();
        });
    });

    describe('calculateHpPercentage', () => {
        it('should calculate correct percentage for full HP', () => {
            expect(calculateHpPercentage(100, 100)).toBe(100);
        });

        it('should calculate correct percentage for half HP', () => {
            expect(calculateHpPercentage(50, 100)).toBe(50);
        });

        it('should calculate correct percentage for partial HP', () => {
            expect(calculateHpPercentage(75, 100)).toBe(75);
        });

        it('should round to nearest integer', () => {
            expect(calculateHpPercentage(33, 100)).toBe(33);
            expect(calculateHpPercentage(1, 3)).toBe(33);
        });

        it('should return 0 for zero max HP', () => {
            expect(calculateHpPercentage(50, 0)).toBe(0);
        });

        it('should return 0 for negative max HP', () => {
            expect(calculateHpPercentage(50, -10)).toBe(0);
        });

        it('should return 0 for negative current HP', () => {
            expect(calculateHpPercentage(-10, 100)).toBe(0);
        });

        it('should return 100 for current HP exceeding max HP', () => {
            expect(calculateHpPercentage(150, 100)).toBe(100);
        });

        it('should handle edge case of 0 current HP', () => {
            expect(calculateHpPercentage(0, 100)).toBe(0);
        });
    });

    describe('isPlayerTurn', () => {
        it('should return true when phase is player_turn', () => {
            const state = createMockCombatState({ phase: 'player_turn' });
            expect(isPlayerTurn(state)).toBe(true);
        });

        it('should return false when phase is enemy_turn', () => {
            const state = createMockCombatState({ phase: 'enemy_turn' });
            expect(isPlayerTurn(state)).toBe(false);
        });

        it('should return false when phase is setup', () => {
            const state = createMockCombatState({ phase: 'setup' });
            expect(isPlayerTurn(state)).toBe(false);
        });

        it('should return false for null state', () => {
            expect(isPlayerTurn(null)).toBe(false);
        });

        it('should return false for undefined state', () => {
            expect(isPlayerTurn(undefined)).toBe(false);
        });

        it('should return false for state without phase', () => {
            expect(isPlayerTurn({})).toBe(false);
        });
    });

    describe('getCurrentTurnCombatant', () => {
        it('should return the current turn combatant', () => {
            const state = createMockCombatState({ current_turn_index: 0 });
            const combatant = getCurrentTurnCombatant(state);
            expect(combatant).toBeDefined();
            expect(combatant.id).toBe('player-1');
        });

        it('should return the enemy when it is their turn', () => {
            const state = createMockCombatState({ current_turn_index: 1 });
            const combatant = getCurrentTurnCombatant(state);
            expect(combatant).toBeDefined();
            expect(combatant.id).toBe('enemy-1');
        });

        it('should return undefined for null state', () => {
            expect(getCurrentTurnCombatant(null)).toBeUndefined();
        });

        it('should return undefined for state without turn_order', () => {
            expect(getCurrentTurnCombatant({ combatants: [] })).toBeUndefined();
        });

        it('should return undefined for invalid turn index', () => {
            const state = createMockCombatState({ current_turn_index: 99 });
            expect(getCurrentTurnCombatant(state)).toBeUndefined();
        });

        it('should return undefined for non-array turn_order', () => {
            expect(getCurrentTurnCombatant({ turn_order: 'invalid' })).toBeUndefined();
        });
    });

    describe('formatHpText', () => {
        it('should format HP as current/max', () => {
            expect(formatHpText(75, 100)).toBe('75/100');
        });

        it('should handle zero values', () => {
            expect(formatHpText(0, 100)).toBe('0/100');
        });

        it('should handle large values', () => {
            expect(formatHpText(9999, 10000)).toBe('9999/10000');
        });
    });

    describe('formatDiceRollText', () => {
        it('should format roll with notation', () => {
            const attackRoll = { notation: '2d6+3' };
            expect(formatDiceRollText(attackRoll, 12)).toBe('2d6+3 = 12');
        });

        it('should format roll without notation', () => {
            expect(formatDiceRollText(null, 15)).toBe('Roll: 15');
        });

        it('should format roll with empty attack object', () => {
            expect(formatDiceRollText({}, 10)).toBe('Roll: 10');
        });

        it('should format roll with attackRoll missing notation', () => {
            expect(formatDiceRollText({ damage: 5 }, 8)).toBe('Roll: 8');
        });
    });

    describe('showCombatHUD', () => {
        it('should set isInCombat to true', () => {
            const state = createMockCombatState();
            showCombatHUD(state);
            expect(window.GameState.isInCombat).toBe(true);
        });

        it('should store combat state in GameState', () => {
            const state = createMockCombatState();
            showCombatHUD(state);
            expect(window.GameState.combatState).toBe(state);
        });

        it('should add active class to combat HUD', () => {
            const state = createMockCombatState();
            showCombatHUD(state);
            expect(window.DOMElements.combatHud.classList.contains('active')).toBe(true);
        });

        it('should disable action input', () => {
            const state = createMockCombatState();
            showCombatHUD(state);
            expect(window.DOMElements.actionInput.disabled).toBe(true);
        });

        it('should disable submit button', () => {
            const state = createMockCombatState();
            showCombatHUD(state);
            expect(window.DOMElements.submitBtn.disabled).toBe(true);
        });

        it('should handle missing DOM elements gracefully', () => {
            window.DOMElements.combatHud = null;
            window.DOMElements.actionInput = null;
            window.DOMElements.submitBtn = null;
            const state = createMockCombatState();
            expect(() => showCombatHUD(state)).not.toThrow();
        });
    });

    describe('hideCombatHUD', () => {
        beforeEach(() => {
            // Set up active combat state
            window.GameState.isInCombat = true;
            window.GameState.combatState = createMockCombatState();
            window.DOMElements.combatHud.classList.add('active');
            window.DOMElements.actionInput.disabled = true;
            window.DOMElements.submitBtn.disabled = true;
        });

        it('should set isInCombat to false', () => {
            hideCombatHUD();
            expect(window.GameState.isInCombat).toBe(false);
        });

        it('should clear combat state', () => {
            hideCombatHUD();
            expect(window.GameState.combatState).toBeNull();
        });

        it('should remove active class from combat HUD', () => {
            hideCombatHUD();
            expect(window.DOMElements.combatHud.classList.contains('active')).toBe(false);
        });

        it('should re-enable action input', () => {
            hideCombatHUD();
            expect(window.DOMElements.actionInput.disabled).toBe(false);
        });

        it('should re-enable submit button', () => {
            hideCombatHUD();
            expect(window.DOMElements.submitBtn.disabled).toBe(false);
        });

        it('should handle missing DOM elements gracefully', () => {
            window.DOMElements.combatHud = null;
            window.DOMElements.actionInput = null;
            window.DOMElements.submitBtn = null;
            expect(() => hideCombatHUD()).not.toThrow();
        });
    });

    describe('updateCombatHUD', () => {
        it('should do nothing for null state', () => {
            expect(() => updateCombatHUD(null)).not.toThrow();
        });

        it('should update player HP bar values', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            expect(window.DOMElements.playerHpBar.value).toBe(100);
            expect(window.DOMElements.playerHpBar.max).toBe(100);
        });

        it('should update player HP text', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            expect(window.DOMElements.playerHpText.textContent).toBe('100/100');
        });

        it('should update enemy name label', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            expect(window.DOMElements.enemyNameLabel.textContent).toBe('Goblin');
        });

        it('should update enemy HP bar values', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            expect(window.DOMElements.enemyHpBar.value).toBe(30);
            expect(window.DOMElements.enemyHpBar.max).toBe(30);
        });

        it('should update enemy HP text', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            expect(window.DOMElements.enemyHpText.textContent).toBe('30/30');
        });

        it('should enable buttons when player turn', () => {
            const state = createMockCombatState({ phase: 'player_turn' });
            updateCombatHUD(state);
            const buttons = document.querySelectorAll('.combat-actions button');
            buttons.forEach(btn => {
                expect(btn.disabled).toBe(false);
            });
        });

        it('should disable buttons when enemy turn', () => {
            const state = createMockCombatState({ phase: 'enemy_turn' });
            updateCombatHUD(state);
            const buttons = document.querySelectorAll('.combat-actions button');
            buttons.forEach(btn => {
                expect(btn.disabled).toBe(true);
            });
        });

        it('should populate turn order list', () => {
            const state = createMockCombatState();
            updateCombatHUD(state);
            const listItems = window.DOMElements.turnOrderList.querySelectorAll('li');
            expect(listItems.length).toBe(2);
        });

        it('should mark active turn with class', () => {
            const state = createMockCombatState({ current_turn_index: 0 });
            updateCombatHUD(state);
            const listItems = window.DOMElements.turnOrderList.querySelectorAll('li');
            expect(listItems[0].classList.contains('active-turn')).toBe(true);
            expect(listItems[1].classList.contains('active-turn')).toBe(false);
        });

        it('should handle missing DOM elements gracefully', () => {
            window.DOMElements.turnOrderList = null;
            window.DOMElements.playerHpBar = null;
            window.DOMElements.enemyHpBar = null;
            const state = createMockCombatState();
            expect(() => updateCombatHUD(state)).not.toThrow();
        });
    });

    describe('showDiceRoll', () => {
        it('should do nothing if diceDisplay is null', () => {
            window.DOMElements.diceDisplay = null;
            expect(() => showDiceRoll({ notation: '1d20' }, 15)).not.toThrow();
        });

        it('should add active class to dice display', () => {
            showDiceRoll({ notation: '1d20' }, 15);
            expect(window.DOMElements.diceDisplay.classList.contains('active')).toBe(true);
        });

        it('should set dice result text with notation', () => {
            showDiceRoll({ notation: '2d6+3' }, 12);
            expect(window.DOMElements.diceResultText.textContent).toBe('2d6+3 = 12');
        });

        it('should set dice result text without notation', () => {
            showDiceRoll(null, 18);
            expect(window.DOMElements.diceResultText.textContent).toBe('Roll: 18');
        });

        it('should remove active class after timeout', () => {
            showDiceRoll({ notation: '1d20' }, 15);
            expect(window.DOMElements.diceDisplay.classList.contains('active')).toBe(true);

            vi.advanceTimersByTime(2000);

            expect(window.DOMElements.diceDisplay.classList.contains('active')).toBe(false);
        });

        it('should trigger dice icon animation', () => {
            showDiceRoll({ notation: '1d20' }, 15);
            const icon = window.DOMElements.diceDisplay.querySelector('.dice-icon');
            expect(icon.style.animation).toBe('dice-spin 0.3s ease-out');
        });
    });

    describe('executeCombatAction', () => {
        beforeEach(() => {
            window.GameState.isInCombat = true;
            window.GameState.sessionId = 'test-session';
            window.GameState.combatState = createMockCombatState();
        });

        it('should not execute if not in combat', async () => {
            const fetchSpy = vi.spyOn(global, 'fetch');
            window.GameState.isInCombat = false;
            await executeCombatAction('attack');
            expect(fetchSpy).not.toHaveBeenCalled();
            fetchSpy.mockRestore();
        });

        it('should not execute if no session ID', async () => {
            const fetchSpy = vi.spyOn(global, 'fetch');
            window.GameState.sessionId = null;
            await executeCombatAction('attack');
            expect(fetchSpy).not.toHaveBeenCalled();
            fetchSpy.mockRestore();
        });

        it('should trigger haptic feedback', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({ success: true, message: 'Attack!' })
            });

            await executeCombatAction('attack');
            expect(window.hapticFeedback).toHaveBeenCalledWith('medium');
        });

        it('should disable buttons during action', async () => {
            let buttonsDisabledDuringFetch = false;

            global.fetch = vi.fn().mockImplementation(() => {
                const buttons = document.querySelectorAll('.combat-actions button');
                buttonsDisabledDuringFetch = Array.from(buttons).every(btn => btn.disabled);
                return Promise.resolve({
                    json: () => Promise.resolve({ success: true, message: 'Attack!' })
                });
            });

            await executeCombatAction('attack');
            expect(buttonsDisabledDuringFetch).toBe(true);
        });

        it('should send correct request body', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({ success: true, message: 'Attack!' })
            });

            await executeCombatAction('attack');

            expect(fetch).toHaveBeenCalledWith('/combat/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: 'test-session',
                    action: 'attack'
                })
            });
        });

        it('should display message on failed action', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({ success: false, message: 'Action failed!' })
            });

            await executeCombatAction('attack');
            expect(window.addMessage).toHaveBeenCalledWith('Action failed!', 'keeper');
        });

        it('should display default message if none provided', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({ success: false })
            });

            await executeCombatAction('attack');
            expect(window.addMessage).toHaveBeenCalledWith('Action failed', 'keeper');
        });

        it('should handle victory scenario', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({
                    success: true,
                    message: 'You hit!',
                    combat_ended: true,
                    victory: true,
                    narrative: 'The goblin falls!'
                })
            });

            await executeCombatAction('attack');

            expect(window.addMessage).toHaveBeenCalledWith('The goblin falls!', 'narrator');
            expect(window.addMessage).toHaveBeenCalledWith('Victory! The enemy has been defeated!', 'keeper');
        });

        it('should handle defeat scenario', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({
                    success: true,
                    message: 'You are hit!',
                    combat_ended: true,
                    victory: false
                })
            });

            await executeCombatAction('defend');

            expect(window.addMessage).toHaveBeenCalledWith('Defeated... You have fallen in battle.', 'keeper');
        });

        it('should handle flee scenario', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({
                    success: true,
                    message: 'You run away!',
                    combat_ended: true,
                    fled: true
                })
            });

            await executeCombatAction('flee');

            expect(window.addMessage).toHaveBeenCalledWith('You escaped from combat!', 'keeper');
        });

        it('should handle network error', async () => {
            global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
            vi.spyOn(console, 'error').mockImplementation(() => {});

            await executeCombatAction('attack');

            expect(window.addMessage).toHaveBeenCalledWith('Combat error occurred', 'keeper');
        });

        it('should hide combat HUD after combat ends', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                json: () => Promise.resolve({
                    success: true,
                    message: 'Victory!',
                    combat_ended: true,
                    victory: true
                })
            });

            window.DOMElements.combatHud.classList.add('active');
            await executeCombatAction('attack');

            vi.advanceTimersByTime(2000);

            expect(window.GameState.isInCombat).toBe(false);
        });
    });

    describe('startCombat', () => {
        it('should show error if no session ID', async () => {
            window.GameState.sessionId = null;
            await startCombat('goblin');
            expect(window.showError).toHaveBeenCalledWith('No active session. Start a new adventure first.');
        });

        it('should send correct request body', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ narrative: 'A goblin appears!', combat_state: createMockCombatState() })
            });

            await startCombat('goblin');

            expect(fetch).toHaveBeenCalledWith('/combat/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: 'test-session-123',
                    enemy_type: 'goblin'
                })
            });
        });

        it('should display narrative message', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ narrative: 'A goblin appears!', combat_state: createMockCombatState() })
            });

            await startCombat('goblin');

            expect(window.addMessage).toHaveBeenCalledWith('A goblin appears!', 'narrator');
        });

        it('should show combat HUD with state', async () => {
            const mockState = createMockCombatState();
            global.fetch = vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ narrative: 'Combat begins!', combat_state: mockState })
            });

            await startCombat('goblin');

            expect(window.GameState.isInCombat).toBe(true);
            expect(window.DOMElements.combatHud.classList.contains('active')).toBe(true);
        });

        it('should handle non-ok response', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                ok: false,
                status: 500
            });
            vi.spyOn(console, 'error').mockImplementation(() => {});

            await startCombat('goblin');

            expect(window.showError).toHaveBeenCalledWith('Failed to start combat: Combat start failed: 500');
        });

        it('should handle network error', async () => {
            global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
            vi.spyOn(console, 'error').mockImplementation(() => {});

            await startCombat('goblin');

            expect(window.showError).toHaveBeenCalledWith('Failed to start combat: Network error');
        });

        it('should not show combat HUD if no combat_state in response', async () => {
            global.fetch = vi.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ narrative: 'Something happens!' })
            });

            await startCombat('goblin');

            expect(window.GameState.isInCombat).toBe(false);
        });
    });

    describe('window exports', () => {
        it('should expose showCombatHUD to window', () => {
            expect(window.showCombatHUD).toBe(showCombatHUD);
        });

        it('should expose hideCombatHUD to window', () => {
            expect(window.hideCombatHUD).toBe(hideCombatHUD);
        });

        it('should expose updateCombatHUD to window', () => {
            expect(window.updateCombatHUD).toBe(updateCombatHUD);
        });

        it('should expose showDiceRoll to window', () => {
            expect(window.showDiceRoll).toBe(showDiceRoll);
        });

        it('should expose executeCombatAction to window', () => {
            expect(window.executeCombatAction).toBe(executeCombatAction);
        });

        it('should expose startCombat to window', () => {
            expect(window.startCombat).toBe(startCombat);
        });

        it('should expose utility functions to window', () => {
            expect(window.createInitialCombatState).toBe(createInitialCombatState);
            expect(window.findCombatantByType).toBe(findCombatantByType);
            expect(window.findCombatantById).toBe(findCombatantById);
            expect(window.calculateHpPercentage).toBe(calculateHpPercentage);
            expect(window.isPlayerTurn).toBe(isPlayerTurn);
            expect(window.getCurrentTurnCombatant).toBe(getCurrentTurnCombatant);
            expect(window.formatHpText).toBe(formatHpText);
            expect(window.formatDiceRollText).toBe(formatDiceRollText);
        });
    });
});
