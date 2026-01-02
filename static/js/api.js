/**
 * Pocket Portals - API Communication
 * Handles all server communication including SSE streaming
 */

'use strict';

/**
 * Handle SSE stream events
 * @param {string} eventType - Event type
 * @param {Object} data - Event data
 */
export function handleStreamEvent(eventType, data) {
    const state = window.GameState;

    switch (eventType) {
        case 'routing':
            console.log('Routing:', data);
            break;

        case 'agent_start':
            window.startStreamingMessage(data.agent);
            window.setLoading(false);
            break;

        case 'agent_chunk':
            window.appendStreamingChar(data.chunk);
            break;

        case 'agent_response':
            if (state.streamingMessageEl) {
                window.endStreamingMessage();
            } else {
                window.addMessage(data.content, data.agent);
            }
            break;

        case 'choices':
            console.log('Received choices:', data.choices);
            window.updateChoices(data.choices);
            break;

        case 'complete':
            state.sessionId = data.session_id;
            window.DOMElements.sessionDisplay.textContent = `Quest: ${data.session_id.substring(0, 8)}...`;
            if (window.GameHeader) {
                window.GameHeader.setQuestTitle('Pocket Portals', `Quest: ${data.session_id.substring(0, 8)}...`);
            }
            break;

        case 'error':
            throw new Error(data.message);

        default:
            if (eventType) {
                console.log('Unknown event type:', eventType, data);
            }
    }
}

/**
 * Send an action to the server with SSE streaming support
 * @param {string|null} action - Custom action text (null if using choice)
 * @param {number|null} choiceIndex - Choice index (1-based, null if using custom action)
 * @returns {Promise<void>}
 */
export async function sendAction(action, choiceIndex) {
    const state = window.GameState;
    const { actionInput, sheetActionInput } = window.DOMElements;

    if (state.isLoading) return;

    window.setLoading(true);
    window.DOMElements.errorDiv.classList.remove('visible');

    // Show player action
    const playerAction = choiceIndex ? state.currentChoices[choiceIndex - 1] : action;
    window.addMessage(playerAction, 'player');

    try {
        const payload = {};

        if (choiceIndex) {
            payload.choice_index = choiceIndex;
        } else {
            payload.action = action;
        }

        if (state.sessionId) {
            payload.session_id = state.sessionId;
        }

        const response = await fetch('/action/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEventType = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('event:')) {
                    currentEventType = line.substring(6).trim();
                } else if (line.startsWith('data:')) {
                    try {
                        const data = JSON.parse(line.substring(5).trim());
                        handleStreamEvent(currentEventType, data);
                    } catch (parseError) {
                        console.warn('Failed to parse SSE data:', parseError);
                    }
                    currentEventType = '';
                }
            }
        }

        // Clear input fields
        if (actionInput) actionInput.value = '';
        if (sheetActionInput) sheetActionInput.value = '';

    } catch (err) {
        console.error('Error:', err);
        window.showError(`Quest failed: ${err.message}`);
    } finally {
        window.setLoading(false);
        if (window.DOMElements.actionInput) {
            window.DOMElements.actionInput.focus();
        }
    }
}

/**
 * Select a choice by index
 * @param {number} index - Choice index (1-based)
 */
export function selectChoice(index) {
    sendAction(null, index);
}

/**
 * Submit the current action from input field
 */
export function submitAction() {
    const { actionInput, sheetActionInput } = window.DOMElements;

    const action = (actionInput && actionInput.value.trim()) ||
                   (sheetActionInput && sheetActionInput.value.trim());

    if (action) {
        sendAction(action);
        if (window.BottomSheet) {
            window.BottomSheet.collapse();
        }
    }
}

/**
 * Start a new adventure
 * @param {boolean} shuffle - Whether to shuffle the starting scenario
 * @returns {Promise<void>}
 */
export async function startNewAdventure(shuffle) {
    const state = window.GameState;
    const { storyBox, actionInput } = window.DOMElements;

    if (typeof shuffle === 'undefined') shuffle = true;

    window.setLoading(true);
    window.DOMElements.errorDiv.classList.remove('visible');

    try {
        const response = await fetch(`/start?shuffle=${shuffle}`);
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        state.sessionId = data.session_id;
        window.DOMElements.sessionDisplay.textContent = `Quest: ${data.session_id.substring(0, 8)}...`;

        if (window.GameHeader) {
            window.GameHeader.setQuestTitle('Pocket Portals', `Quest: ${data.session_id.substring(0, 8)}...`);
            window.GameHeader.updateTurn(1);
        }

        if (storyBox) {
            storyBox.innerHTML = '';
        }
        window.addMessage(data.narrative, 'narrator');
        window.updateChoices(data.choices);

    } catch (err) {
        console.error('Error:', err);
        window.showError(`Failed to start adventure: ${err.message}`);
    } finally {
        window.setLoading(false);
        if (actionInput) {
            actionInput.focus();
        }
    }
}

/**
 * Reset to new game state
 */
export function newGame() {
    const state = window.GameState;
    const { storyBox, choicesSection, actionInput, sheetActionInput, sessionDisplay } = window.DOMElements;

    state.sessionId = null;
    state.currentChoices = [];
    state.turnCount = 1;

    if (sessionDisplay) {
        sessionDisplay.textContent = 'New Adventure';
    }

    if (choicesSection) {
        choicesSection.classList.add('hidden');
    }

    if (window.BottomSheet) {
        window.BottomSheet.hide();
    }

    if (window.GameHeader) {
        window.GameHeader.updateTurn(1);
        window.GameHeader.setQuestTitle('Pocket Portals', 'New Adventure');
    }

    if (storyBox) {
        storyBox.innerHTML = `
            <div class="welcome">
                <i class="ra ra-scroll-unfurled"></i>
                <h2>Welcome, Adventurer!</h2>
                <p>Your quest awaits. Choose your starting path or type your own action below.</p>
                <button class="nes-btn is-primary begin-btn" id="begin-btn">
                    <i class="ra ra-player-lift"></i> Begin Quest
                </button>
            </div>
        `;
    }

    if (actionInput) {
        actionInput.value = '';
    }

    if (sheetActionInput) {
        sheetActionInput.value = '';
    }

    if (actionInput) {
        actionInput.focus();
    }
}

// Expose functions to window for backward compatibility
if (typeof window !== 'undefined') {
    window.sendAction = sendAction;
    window.selectChoice = selectChoice;
    window.submitAction = submitAction;
    window.startNewAdventure = startNewAdventure;
    window.newGame = newGame;
    window.handleStreamEvent = handleStreamEvent;
}
