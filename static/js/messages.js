/**
 * Pocket Portals - Message Functions
 * Handles message display, streaming, and UI updates
 */

(function() {
    'use strict';

    /**
     * Add a complete message to the story box
     * @param {string} text - Message text content
     * @param {string} type - Message type (narrator, keeper, jester, player)
     */
    function addMessage(text, type) {
        const { storyBox } = window.DOMElements;
        if (!storyBox) return;

        // Remove welcome if present
        const welcome = storyBox.querySelector('.welcome');
        if (welcome) welcome.remove();

        const div = document.createElement('div');
        div.className = `message message-${type}`;

        const config = window.AgentConfig[type] || window.AgentConfig.narrator;
        const formattedText = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');

        div.innerHTML = `
            <div class="message-label"><i class="ra ${config.icon}"></i> ${config.label}</div>
            <div class="message-text"><p>${formattedText}</p></div>
        `;

        storyBox.appendChild(div);
        storyBox.scrollTop = storyBox.scrollHeight;
    }

    /**
     * Start a new streaming message
     * @param {string} type - Agent type (narrator, keeper, jester, player)
     */
    function startStreamingMessage(type) {
        const { storyBox } = window.DOMElements;
        const state = window.GameState;

        if (!storyBox) return;

        // Remove welcome if present
        const welcome = storyBox.querySelector('.welcome');
        if (welcome) welcome.remove();

        state.currentAgent = type;

        // Show response indicator
        if (window.ResponseIndicator) {
            window.ResponseIndicator.show(type);
        }

        // Create the message container
        state.streamingMessageEl = document.createElement('div');
        state.streamingMessageEl.className = `message message-${type}`;

        const config = window.AgentConfig[type] || window.AgentConfig.narrator;

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
    function appendStreamingChar(char) {
        const state = window.GameState;
        const { storyBox } = window.DOMElements;

        if (!state.streamingTextEl) return;

        state.streamingContent += char;
        const formattedText = state.streamingContent
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
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
    function endStreamingMessage() {
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
     * Update choices in both desktop and mobile (bottom sheet) views
     * @param {Array<string>} choices - Array of choice strings
     */
    function updateChoices(choices) {
        console.log('updateChoices called with:', choices);

        const state = window.GameState;
        const { choicesSection, choicesDiv } = window.DOMElements;

        state.currentChoices = choices || [];

        // Update desktop choices
        if (state.currentChoices.length > 0) {
            if (choicesSection) {
                choicesSection.classList.remove('hidden');
            }

            if (choicesDiv) {
                choicesDiv.innerHTML = '';
                const icons = ['ra-axe', 'ra-speech-bubble', 'ra-boot-stomp'];

                state.currentChoices.forEach((choice, i) => {
                    const btn = document.createElement('button');
                    btn.className = 'nes-btn choice-btn';
                    btn.innerHTML = `<i class="ra ${icons[i] || 'ra-hand'}"></i> ${choice}`;
                    btn.onclick = () => {
                        if (typeof window.selectChoice === 'function') {
                            window.selectChoice(i + 1);
                        }
                    };
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
    function setLoading(loading) {
        const state = window.GameState;
        const { loadingDiv, submitBtn, actionInput, choicesSection } = window.DOMElements;

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
    function showError(message) {
        const { errorDiv } = window.DOMElements;

        if (!errorDiv) return;

        errorDiv.textContent = message;
        errorDiv.classList.add('visible');

        setTimeout(() => {
            errorDiv.classList.remove('visible');
        }, 5000);
    }

    // Expose functions to window
    window.addMessage = addMessage;
    window.startStreamingMessage = startStreamingMessage;
    window.appendStreamingChar = appendStreamingChar;
    window.endStreamingMessage = endStreamingMessage;
    window.updateChoices = updateChoices;
    window.setLoading = setLoading;
    window.showError = showError;

})();
