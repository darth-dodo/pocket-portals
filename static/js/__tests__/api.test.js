/**
 * Tests for api.js - API Communication Module
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    sendAction,
    selectChoice,
    submitAction,
    startNewAdventure,
    newGame,
    handleStreamEvent
} from '../api.js';

// Helper to create mock SSE response
function createMockSSEResponse(events) {
    const encoder = new TextEncoder();
    let chunks = [];

    for (const event of events) {
        let sseText = '';
        if (event.type) {
            sseText += `event:${event.type}\n`;
        }
        sseText += `data:${JSON.stringify(event.data)}\n\n`;
        chunks.push(encoder.encode(sseText));
    }

    let chunkIndex = 0;
    return {
        ok: true,
        body: {
            getReader: () => ({
                read: vi.fn().mockImplementation(() => {
                    if (chunkIndex < chunks.length) {
                        return Promise.resolve({ done: false, value: chunks[chunkIndex++] });
                    }
                    return Promise.resolve({ done: true, value: undefined });
                })
            })
        }
    };
}

describe('API Communication Module', () => {
    let mockGameState;
    let mockDOMElements;

    beforeEach(() => {
        // Reset mocks
        vi.clearAllMocks();

        // Setup mock GameState
        mockGameState = {
            sessionId: null,
            currentChoices: ['Attack', 'Defend', 'Run'],
            isLoading: false,
            turnCount: 1,
            streamingMessageEl: null,
            streamingTextEl: null,
            streamingContent: '',
            currentAgent: 'narrator'
        };
        window.GameState = mockGameState;

        // Setup mock DOMElements
        mockDOMElements = {
            actionInput: { value: '', focus: vi.fn() },
            sheetActionInput: { value: '' },
            storyBox: { innerHTML: '' },
            choicesSection: { classList: { add: vi.fn(), remove: vi.fn() } },
            choicesDiv: {},
            errorDiv: { classList: { add: vi.fn(), remove: vi.fn() } },
            sessionDisplay: { textContent: '' },
            loadingDiv: {}
        };
        window.DOMElements = mockDOMElements;

        // Setup mock window functions
        window.setLoading = vi.fn();
        window.showError = vi.fn();
        window.addMessage = vi.fn();
        window.updateChoices = vi.fn();
        window.startStreamingMessage = vi.fn();
        window.appendStreamingChar = vi.fn();
        window.endStreamingMessage = vi.fn();
        window.BottomSheet = { collapse: vi.fn(), hide: vi.fn() };
        window.GameHeader = {
            setQuestTitle: vi.fn(),
            updateTurn: vi.fn()
        };

        // Mock console methods
        vi.spyOn(console, 'error').mockImplementation(() => {});
        vi.spyOn(console, 'warn').mockImplementation(() => {});
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('handleStreamEvent', () => {
        it('should handle routing event', () => {
            handleStreamEvent('routing', { path: '/action' });
            // Routing just logs, no side effects to verify
        });

        it('should handle agent_start event', () => {
            handleStreamEvent('agent_start', { agent: 'narrator' });

            expect(window.startStreamingMessage).toHaveBeenCalledWith('narrator');
            expect(window.setLoading).toHaveBeenCalledWith(false);
        });

        it('should handle agent_chunk event', () => {
            handleStreamEvent('agent_chunk', { chunk: 'Hello' });

            expect(window.appendStreamingChar).toHaveBeenCalledWith('Hello');
        });

        it('should handle agent_response with streaming message element', () => {
            mockGameState.streamingMessageEl = document.createElement('div');

            handleStreamEvent('agent_response', { content: 'Full story', agent: 'narrator' });

            expect(window.endStreamingMessage).toHaveBeenCalled();
            expect(window.addMessage).not.toHaveBeenCalled();
        });

        it('should handle agent_response without streaming message element', () => {
            mockGameState.streamingMessageEl = null;

            handleStreamEvent('agent_response', { content: 'Full story', agent: 'narrator' });

            expect(window.addMessage).toHaveBeenCalledWith('Full story', 'narrator');
            expect(window.endStreamingMessage).not.toHaveBeenCalled();
        });

        it('should handle choices event', () => {
            const choices = ['Option A', 'Option B'];

            handleStreamEvent('choices', { choices });

            expect(window.updateChoices).toHaveBeenCalledWith(choices);
        });

        it('should handle complete event', () => {
            handleStreamEvent('complete', { session_id: 'abc123456789' });

            expect(mockGameState.sessionId).toBe('abc123456789');
            expect(mockDOMElements.sessionDisplay.textContent).toBe('Quest: abc12345...');
            expect(window.GameHeader.setQuestTitle).toHaveBeenCalledWith(
                'Pocket Portals',
                'Quest: abc12345...'
            );
        });

        it('should handle complete event without GameHeader', () => {
            window.GameHeader = null;

            handleStreamEvent('complete', { session_id: 'xyz987654321' });

            expect(mockGameState.sessionId).toBe('xyz987654321');
            expect(mockDOMElements.sessionDisplay.textContent).toBe('Quest: xyz98765...');
        });

        it('should throw error on error event', () => {
            expect(() => {
                handleStreamEvent('error', { message: 'Something went wrong' });
            }).toThrow('Something went wrong');
        });

        it('should handle unknown event types gracefully', () => {
            // Should not throw
            expect(() => {
                handleStreamEvent('unknown_event', { data: 'test' });
            }).not.toThrow();
        });

        it('should ignore empty event types', () => {
            expect(() => {
                handleStreamEvent('', { data: 'test' });
            }).not.toThrow();
        });
    });

    describe('sendAction', () => {
        beforeEach(() => {
            global.fetch = vi.fn();
        });

        it('should not send action when already loading', async () => {
            mockGameState.isLoading = true;

            await sendAction('test action', null);

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should send custom action with correct payload', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('I attack the dragon', null);

            expect(global.fetch).toHaveBeenCalledWith('/action/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'I attack the dragon' })
            });
        });

        it('should send choice index with correct payload', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction(null, 2);

            expect(global.fetch).toHaveBeenCalledWith('/action/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ choice_index: 2 })
            });
        });

        it('should include session_id when available', async () => {
            mockGameState.sessionId = 'existing-session';
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('test', null);

            expect(global.fetch).toHaveBeenCalledWith('/action/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'test', session_id: 'existing-session' })
            });
        });

        it('should display player action message for custom action', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('I cast fireball', null);

            expect(window.addMessage).toHaveBeenCalledWith('I cast fireball', 'player');
        });

        it('should display player action message for choice selection', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction(null, 1);

            expect(window.addMessage).toHaveBeenCalledWith('Attack', 'player');
        });

        it('should set loading state correctly', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('test', null);

            expect(window.setLoading).toHaveBeenCalledWith(true);
            expect(window.setLoading).toHaveBeenCalledWith(false);
        });

        it('should clear input fields after successful action', async () => {
            mockDOMElements.actionInput.value = 'test input';
            mockDOMElements.sheetActionInput.value = 'sheet input';
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('test', null);

            expect(mockDOMElements.actionInput.value).toBe('');
            expect(mockDOMElements.sheetActionInput.value).toBe('');
        });

        it('should handle server error response', async () => {
            global.fetch.mockResolvedValue({ ok: false, status: 500 });

            await sendAction('test', null);

            expect(window.showError).toHaveBeenCalledWith('Quest failed: Server error: 500');
        });

        it('should handle network error', async () => {
            global.fetch.mockRejectedValue(new Error('Network error'));

            await sendAction('test', null);

            expect(window.showError).toHaveBeenCalledWith('Quest failed: Network error');
        });

        it('should process SSE events correctly', async () => {
            const mockResponse = createMockSSEResponse([
                { type: 'agent_start', data: { agent: 'narrator' } },
                { type: 'agent_chunk', data: { chunk: 'Hello ' } },
                { type: 'agent_chunk', data: { chunk: 'world' } },
                { type: 'complete', data: { session_id: 'new-session-id' } }
            ]);
            global.fetch.mockResolvedValue(mockResponse);

            await sendAction('test', null);

            expect(window.startStreamingMessage).toHaveBeenCalledWith('narrator');
            expect(window.appendStreamingChar).toHaveBeenCalledWith('Hello ');
            expect(window.appendStreamingChar).toHaveBeenCalledWith('world');
        });

        it('should focus action input after completion', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('test', null);

            expect(mockDOMElements.actionInput.focus).toHaveBeenCalled();
        });

        it('should hide error div at start', async () => {
            global.fetch.mockResolvedValue(createMockSSEResponse([]));

            await sendAction('test', null);

            expect(mockDOMElements.errorDiv.classList.remove).toHaveBeenCalledWith('visible');
        });
    });

    describe('selectChoice', () => {
        beforeEach(() => {
            global.fetch = vi.fn().mockResolvedValue(createMockSSEResponse([]));
        });

        it('should call sendAction with null action and provided index', async () => {
            await selectChoice(2);

            expect(window.addMessage).toHaveBeenCalledWith('Defend', 'player');
        });
    });

    describe('submitAction', () => {
        beforeEach(() => {
            global.fetch = vi.fn().mockResolvedValue(createMockSSEResponse([]));
        });

        it('should submit action from actionInput', async () => {
            mockDOMElements.actionInput.value = '  I explore the cave  ';

            submitAction();

            await vi.waitFor(() => {
                expect(window.addMessage).toHaveBeenCalledWith('I explore the cave', 'player');
            });
        });

        it('should submit action from sheetActionInput when actionInput is empty', async () => {
            mockDOMElements.actionInput.value = '';
            mockDOMElements.sheetActionInput.value = 'sheet action';

            submitAction();

            await vi.waitFor(() => {
                expect(window.addMessage).toHaveBeenCalledWith('sheet action', 'player');
            });
        });

        it('should not submit empty action', () => {
            mockDOMElements.actionInput.value = '   ';
            mockDOMElements.sheetActionInput.value = '';

            submitAction();

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should collapse bottom sheet after submitting', async () => {
            mockDOMElements.actionInput.value = 'test action';

            submitAction();

            expect(window.BottomSheet.collapse).toHaveBeenCalled();
        });

        it('should handle missing BottomSheet', async () => {
            window.BottomSheet = null;
            mockDOMElements.actionInput.value = 'test action';

            expect(() => submitAction()).not.toThrow();
        });
    });

    describe('startNewAdventure', () => {
        beforeEach(() => {
            global.fetch = vi.fn();
        });

        it('should fetch with shuffle=true by default', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'new-adventure-id',
                    narrative: 'Your adventure begins...',
                    choices: ['Go left', 'Go right']
                })
            });

            await startNewAdventure();

            expect(global.fetch).toHaveBeenCalledWith('/start?shuffle=true');
        });

        it('should fetch with shuffle=false when specified', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'Story',
                    choices: []
                })
            });

            await startNewAdventure(false);

            expect(global.fetch).toHaveBeenCalledWith('/start?shuffle=false');
        });

        it('should update session state on success', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'adventure-123',
                    narrative: 'The story unfolds...',
                    choices: ['Option 1', 'Option 2']
                })
            });

            await startNewAdventure(true);

            expect(mockGameState.sessionId).toBe('adventure-123');
            expect(mockDOMElements.sessionDisplay.textContent).toBe('Quest: adventur...');
        });

        it('should clear story box and add narrative message', async () => {
            mockDOMElements.storyBox.innerHTML = '<div>Old content</div>';
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'New adventure begins!',
                    choices: []
                })
            });

            await startNewAdventure(true);

            expect(mockDOMElements.storyBox.innerHTML).toBe('');
            expect(window.addMessage).toHaveBeenCalledWith('New adventure begins!', 'narrator');
        });

        it('should update choices', async () => {
            const choices = ['Fight', 'Flee', 'Negotiate'];
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'Story',
                    choices
                })
            });

            await startNewAdventure(true);

            expect(window.updateChoices).toHaveBeenCalledWith(choices);
        });

        it('should update GameHeader on success', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'header-test',
                    narrative: 'Story',
                    choices: []
                })
            });

            await startNewAdventure(true);

            expect(window.GameHeader.setQuestTitle).toHaveBeenCalledWith(
                'Pocket Portals',
                'Quest: header-t...'
            );
            expect(window.GameHeader.updateTurn).toHaveBeenCalledWith(1);
        });

        it('should handle missing GameHeader', async () => {
            window.GameHeader = null;
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'Story',
                    choices: []
                })
            });

            await expect(startNewAdventure(true)).resolves.not.toThrow();
        });

        it('should handle server error', async () => {
            global.fetch.mockResolvedValue({ ok: false, status: 503 });

            await startNewAdventure(true);

            expect(window.showError).toHaveBeenCalledWith('Failed to start adventure: Server error: 503');
        });

        it('should handle network error', async () => {
            global.fetch.mockRejectedValue(new Error('Connection refused'));

            await startNewAdventure(true);

            expect(window.showError).toHaveBeenCalledWith('Failed to start adventure: Connection refused');
        });

        it('should set loading state correctly', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'Story',
                    choices: []
                })
            });

            await startNewAdventure(true);

            expect(window.setLoading).toHaveBeenCalledWith(true);
            expect(window.setLoading).toHaveBeenCalledWith(false);
        });

        it('should focus action input after completion', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    session_id: 'test-id',
                    narrative: 'Story',
                    choices: []
                })
            });

            await startNewAdventure(true);

            expect(mockDOMElements.actionInput.focus).toHaveBeenCalled();
        });
    });

    describe('newGame', () => {
        it('should reset game state', () => {
            mockGameState.sessionId = 'old-session';
            mockGameState.currentChoices = ['old choice'];
            mockGameState.turnCount = 5;

            newGame();

            expect(mockGameState.sessionId).toBeNull();
            expect(mockGameState.currentChoices).toEqual([]);
            expect(mockGameState.turnCount).toBe(1);
        });

        it('should update session display', () => {
            newGame();

            expect(mockDOMElements.sessionDisplay.textContent).toBe('New Adventure');
        });

        it('should hide choices section', () => {
            newGame();

            expect(mockDOMElements.choicesSection.classList.add).toHaveBeenCalledWith('hidden');
        });

        it('should hide bottom sheet', () => {
            newGame();

            expect(window.BottomSheet.hide).toHaveBeenCalled();
        });

        it('should update GameHeader', () => {
            newGame();

            expect(window.GameHeader.updateTurn).toHaveBeenCalledWith(1);
            expect(window.GameHeader.setQuestTitle).toHaveBeenCalledWith('Pocket Portals', 'New Adventure');
        });

        it('should set welcome HTML in story box', () => {
            newGame();

            expect(mockDOMElements.storyBox.innerHTML).toContain('Welcome, Adventurer!');
            expect(mockDOMElements.storyBox.innerHTML).toContain('begin-btn');
        });

        it('should clear input fields', () => {
            mockDOMElements.actionInput.value = 'old input';
            mockDOMElements.sheetActionInput.value = 'old sheet input';

            newGame();

            expect(mockDOMElements.actionInput.value).toBe('');
            expect(mockDOMElements.sheetActionInput.value).toBe('');
        });

        it('should focus action input', () => {
            newGame();

            expect(mockDOMElements.actionInput.focus).toHaveBeenCalled();
        });

        it('should handle missing optional elements gracefully', () => {
            mockDOMElements.sessionDisplay = null;
            mockDOMElements.choicesSection = null;
            mockDOMElements.storyBox = null;
            mockDOMElements.actionInput = null;
            mockDOMElements.sheetActionInput = null;
            window.BottomSheet = null;
            window.GameHeader = null;

            expect(() => newGame()).not.toThrow();
        });
    });

    describe('window exports', () => {
        it('should expose all functions to window', () => {
            expect(window.sendAction).toBe(sendAction);
            expect(window.selectChoice).toBe(selectChoice);
            expect(window.submitAction).toBe(submitAction);
            expect(window.startNewAdventure).toBe(startNewAdventure);
            expect(window.newGame).toBe(newGame);
            expect(window.handleStreamEvent).toBe(handleStreamEvent);
        });
    });
});
