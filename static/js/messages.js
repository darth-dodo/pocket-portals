/**
 * Pocket Portals - Message Functions
 * Handles message display, streaming, and UI updates
 */

'use strict';

/**
 * Format text by replacing newlines with HTML breaks and paragraphs
 * @param {string} text - Raw text to format
 * @returns {string} HTML-formatted text
 */
export function formatMessageText(text) {
    return text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
}

/**
 * Create a message element with proper structure
 * @param {string} type - Message type (narrator, keeper, jester, player)
 * @param {Object} config - Agent configuration with icon and label
 * @param {string} textHtml - HTML content for the message text
 * @returns {HTMLDivElement} The created message element
 */
export function createMessageElement(type, config, textHtml) {
    const div = document.createElement('div');
    div.className = `message message-${type}`;

    div.innerHTML = `
        <div class="message-label"><i class="ra ${config.icon}"></i> ${config.label}</div>
        <div class="message-text"><p>${textHtml}</p></div>
    `;

    return div;
}

/**
 * Remove welcome element from story box if present
 * @param {HTMLElement} storyBox - The story box container
 * @returns {boolean} True if welcome was removed, false otherwise
 */
export function removeWelcomeIfPresent(storyBox) {
    if (!storyBox) return false;
    const welcome = storyBox.querySelector('.welcome');
    if (welcome) {
        welcome.remove();
        return true;
    }
    return false;
}

/**
 * Add a complete message to the story box
 * @param {string} text - Message text content
 * @param {string} type - Message type (narrator, keeper, jester, player)
 */
export function addMessage(text, type) {
    const { storyBox } = window.DOMElements || {};
    if (!storyBox) return;

    removeWelcomeIfPresent(storyBox);

    const config = window.AgentConfig?.[type] || window.AgentConfig?.narrator || { icon: 'ra-scroll-unfurled', label: 'Narrator' };
    const formattedText = formatMessageText(text);

    const div = createMessageElement(type, config, formattedText);

    storyBox.appendChild(div);
    storyBox.scrollTop = storyBox.scrollHeight;
}

/**
 * Start a new streaming message
 * @param {string} type - Agent type (narrator, keeper, jester, player)
 */
export function startStreamingMessage(type) {
    const { storyBox } = window.DOMElements || {};
    const state = window.GameState;

    if (!storyBox) return;

    removeWelcomeIfPresent(storyBox);

    state.currentAgent = type;

    // Show response indicator
    if (window.ResponseIndicator) {
        window.ResponseIndicator.show(type);
    }

    // Create the message container
    state.streamingMessageEl = document.createElement('div');
    state.streamingMessageEl.className = `message message-${type}`;

    const config = window.AgentConfig?.[type] || window.AgentConfig?.narrator || { icon: 'ra-scroll-unfurled', label: 'Narrator' };

    state.streamingMessageEl.innerHTML = `
        <div class="message-label"><i class="ra ${config.icon}"></i> ${config.label}</div>
        <div class="message-text"><p class="streaming-text"></p></div>
    `;

    storyBox.appendChild(state.streamingMessageEl);
    state.streamingTextEl = state.streamingMessageEl.querySelector('.streaming-text');
    state.streamingContent = '';
}

/**
 * Append a character to the current streaming message
 * @param {string} char - Character to append
 */
export function appendStreamingChar(char) {
    const state = window.GameState;
    const { storyBox } = window.DOMElements || {};

    if (!state.streamingTextEl) return;

    state.streamingContent += char;
    const formattedText = formatMessageText(state.streamingContent);
    state.streamingTextEl.innerHTML = formattedText;

    // Throttle scroll updates for performance
    const now = Date.now();
    if (now - state.lastScrollTime >= state.SCROLL_THROTTLE_MS) {
        state.lastScrollTime = now;
        requestAnimationFrame(() => {
            if (storyBox) {
                storyBox.scrollTop = storyBox.scrollHeight;
            }
        });
    }
}

/**
 * End the current streaming message
 */
export function endStreamingMessage() {
    const state = window.GameState;

    // Hide response indicator
    if (window.ResponseIndicator) {
        window.ResponseIndicator.hide();
    }

    // Remove blinking cursor
    if (state.streamingTextEl) {
        state.streamingTextEl.classList.remove('streaming-text');
    }

    // Clear streaming state
    state.streamingMessageEl = null;
    state.streamingTextEl = null;
    state.streamingContent = '';

    // Update turn counter
    if (window.GameHeader) {
        window.GameHeader.updateTurn(state.turnCount + 1);
    }
}

/**
 * Create a choice button element
 * @param {string} choice - Choice text
 * @param {number} index - Choice index (0-based)
 * @param {string} iconClass - Icon class name
 * @returns {HTMLButtonElement} The created button element
 */
export function createChoiceButton(choice, index, iconClass) {
    const btn = document.createElement('button');
    btn.className = 'nes-btn choice-btn';
    btn.innerHTML = `<i class="ra ${iconClass}"></i> ${choice}`;
    btn.onclick = () => {
        // Trigger haptic feedback for choice selection
        if (typeof window.hapticFeedback === 'function') {
            window.hapticFeedback('light');
        }
        if (typeof window.selectChoice === 'function') {
            window.selectChoice(index + 1);
        }
    };
    return btn;
}

/**
 * Get icon class for a choice by index
 * @param {number} index - Choice index (0-based)
 * @returns {string} Icon class name
 */
export function getChoiceIcon(index) {
    const icons = ['ra-axe', 'ra-speech-bubble', 'ra-boot-stomp'];
    return icons[index] || 'ra-hand';
}

/**
 * Update choices in both desktop and mobile (bottom sheet) views
 * @param {Array<string>} choices - Array of choice strings
 */
export function updateChoices(choices) {
    console.log('updateChoices called with:', choices);

    const state = window.GameState;
    const { choicesSection, choicesDiv } = window.DOMElements || {};

    state.currentChoices = choices || [];

    // Update desktop choices
    if (state.currentChoices.length > 0) {
        if (choicesSection) {
            choicesSection.classList.remove('hidden');
        }

        if (choicesDiv) {
            choicesDiv.innerHTML = '';

            state.currentChoices.forEach((choice, i) => {
                const btn = createChoiceButton(choice, i, getChoiceIcon(i));
                choicesDiv.appendChild(btn);
            });
        }
    } else {
        if (choicesSection) {
            choicesSection.classList.add('hidden');
        }
    }

    // Update mobile bottom sheet
    if (window.BottomSheet) {
        window.BottomSheet.updateChoices(state.currentChoices);
    }
}

/**
 * Set loading state for the UI
 * @param {boolean} loading - Whether the UI is in loading state
 */
export function setLoading(loading) {
    const state = window.GameState;
    const { loadingDiv, submitBtn, actionInput, choicesSection } = window.DOMElements || {};

    state.isLoading = loading;

    if (loadingDiv) {
        loadingDiv.classList.toggle('visible', loading);
    }

    if (submitBtn) {
        submitBtn.disabled = loading;
    }

    if (actionInput) {
        actionInput.disabled = loading;
    }

    if (loading) {
        // Set random loading phrase
        const loadingText = document.getElementById('loading-text');
        if (loadingText && typeof window.getRandomLoadingPhrase === 'function') {
            loadingText.textContent = window.getRandomLoadingPhrase();
        }

        if (choicesSection) {
            choicesSection.classList.add('hidden');
        }

        if (window.BottomSheet) {
            window.BottomSheet.hide();
        }
    }

    // Disable/enable choice buttons
    document.querySelectorAll('.choice-btn').forEach(btn => {
        btn.disabled = loading;
    });
}

/**
 * Show an error message
 * @param {string} message - Error message to display
 */
export function showError(message) {
    const { errorDiv } = window.DOMElements || {};

    if (!errorDiv) return;

    errorDiv.textContent = message;
    errorDiv.classList.add('visible');

    setTimeout(() => {
        errorDiv.classList.remove('visible');
    }, 5000);
}

// Expose functions to window for backward compatibility
if (typeof window !== 'undefined') {
    window.addMessage = addMessage;
    window.startStreamingMessage = startStreamingMessage;
    window.appendStreamingChar = appendStreamingChar;
    window.endStreamingMessage = endStreamingMessage;
    window.updateChoices = updateChoices;
    window.setLoading = setLoading;
    window.showError = showError;
    // Also expose helper functions for potential reuse
    window.formatMessageText = formatMessageText;
    window.createMessageElement = createMessageElement;
    window.removeWelcomeIfPresent = removeWelcomeIfPresent;
    window.createChoiceButton = createChoiceButton;
    window.getChoiceIcon = getChoiceIcon;
}
