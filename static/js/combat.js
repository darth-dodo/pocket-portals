/**
 * Pocket Portals - Combat System
 * Handles combat HUD, dice rolls, and combat actions
 */

(function() {
    'use strict';

    /**
     * Show the combat HUD with initial state
     * @param {Object} state - Combat state object
     */
    function showCombatHUD(state) {
        const gameState = window.GameState;
        const { combatHud, actionInput, submitBtn } = window.DOMElements;

        gameState.combatState = state;
        gameState.isInCombat = true;

        if (combatHud) {
            combatHud.classList.add('active');
        }

        updateCombatHUD(state);

        // Disable regular input during combat
        if (actionInput) actionInput.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
    }

    /**
     * Hide the combat HUD
     */
    function hideCombatHUD() {
        const gameState = window.GameState;
        const { combatHud, actionInput, submitBtn } = window.DOMElements;

        gameState.isInCombat = false;
        gameState.combatState = null;

        if (combatHud) {
            combatHud.classList.remove('active');
        }

        // Re-enable regular input
        if (actionInput) actionInput.disabled = false;
        if (submitBtn) submitBtn.disabled = false;
    }

    /**
     * Update the combat HUD display with current state
     * @param {Object} state - Combat state object
     */
    function updateCombatHUD(state) {
        if (!state) return;

        const {
            turnOrderList,
            playerHpBar,
            playerHpText,
            enemyNameLabel,
            enemyHpBar,
            enemyHpText
        } = window.DOMElements;

        // Update turn order list
        if (turnOrderList) {
            turnOrderList.innerHTML = '';

            state.turn_order.forEach((id, index) => {
                const combatant = state.combatants.find(c => c.id === id);
                if (combatant) {
                    const li = document.createElement('li');
                    const icon = combatant.type === 'player' ? 'ra-player' : 'ra-skull';
                    li.innerHTML = `<i class="ra ${icon}"></i> ${combatant.name}`;

                    if (index === state.current_turn_index) {
                        li.classList.add('active-turn');
                    }
                    turnOrderList.appendChild(li);
                }
            });
        }

        // Find player and enemy combatants
        const player = state.combatants.find(c => c.type === 'player');
        const enemy = state.combatants.find(c => c.type === 'enemy');

        // Update player HP display
        if (player) {
            if (playerHpBar) {
                playerHpBar.value = player.current_hp;
                playerHpBar.max = player.max_hp;
            }
            if (playerHpText) {
                playerHpText.textContent = `${player.current_hp}/${player.max_hp}`;
            }
        }

        // Update enemy HP display
        if (enemy) {
            if (enemyNameLabel) {
                enemyNameLabel.textContent = enemy.name;
            }
            if (enemyHpBar) {
                enemyHpBar.value = enemy.current_hp;
                enemyHpBar.max = enemy.max_hp;
            }
            if (enemyHpText) {
                enemyHpText.textContent = `${enemy.current_hp}/${enemy.max_hp}`;
            }
        }

        // Enable/disable combat action buttons based on turn
        const isPlayerTurn = state.phase === 'player_turn';
        const buttons = document.querySelectorAll('.combat-actions button');
        buttons.forEach(btn => {
            btn.disabled = !isPlayerTurn;
        });
    }

    /**
     * Show dice roll animation and result
     * @param {Object} attackRoll - Attack roll object with notation
     * @param {number} total - Total roll result
     */
    function showDiceRoll(attackRoll, total) {
        const { diceDisplay, diceResultText } = window.DOMElements;

        if (!diceDisplay) return;

        diceDisplay.classList.add('active');

        if (diceResultText) {
            if (attackRoll && attackRoll.notation) {
                diceResultText.textContent = `${attackRoll.notation} = ${total}`;
            } else {
                diceResultText.textContent = `Roll: ${total}`;
            }
        }

        // Animate dice icon
        const icon = diceDisplay.querySelector('.dice-icon');
        if (icon) {
            icon.style.animation = 'none';
            // Force reflow
            void icon.offsetHeight;
            icon.style.animation = 'dice-spin 0.3s ease-out';
        }

        // Hide after delay
        setTimeout(() => {
            diceDisplay.classList.remove('active');
        }, 2000);
    }

    /**
     * Execute a combat action
     * @param {string} action - Combat action (attack, defend, flee)
     * @returns {Promise<void>}
     */
    async function executeCombatAction(action) {
        const gameState = window.GameState;

        if (!gameState.isInCombat || !gameState.sessionId) return;

        // Trigger haptic feedback for combat action
        if (typeof window.hapticFeedback === 'function') {
            window.hapticFeedback('medium');
        }

        // Disable buttons during action
        const buttons = document.querySelectorAll('.combat-actions button');
        buttons.forEach(btn => btn.disabled = true);

        try {
            const response = await fetch('/combat/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: gameState.sessionId,
                    action: action
                })
            });

            const data = await response.json();

            if (!data.success) {
                window.addMessage(data.message || 'Action failed', 'keeper');
                return;
            }

            // Show dice roll if present
            if (data.result && data.result.attack_roll) {
                showDiceRoll(data.result.attack_roll, data.result.total_attack);
            }

            // Add action message
            window.addMessage(data.message, 'keeper');

            // Update combat HUD
            updateCombatHUD(data.combat_state);

            // Handle combat end
            if (data.combat_ended) {
                if (data.narrative) {
                    window.addMessage(data.narrative, 'narrator');
                }

                if (data.victory === true) {
                    window.addMessage('Victory! The enemy has been defeated!', 'keeper');
                } else if (data.victory === false) {
                    window.addMessage('Defeated... You have fallen in battle.', 'keeper');
                } else if (data.fled) {
                    window.addMessage('You escaped from combat!', 'keeper');
                }

                // Hide combat HUD after delay
                setTimeout(() => {
                    hideCombatHUD();
                }, 2000);
            }

        } catch (error) {
            console.error('Combat action error:', error);
            window.addMessage('Combat error occurred', 'keeper');
        } finally {
            // Re-enable buttons if still in combat and player turn
            if (gameState.isInCombat && gameState.combatState && gameState.combatState.phase === 'player_turn') {
                buttons.forEach(btn => btn.disabled = false);
            }
        }
    }

    /**
     * Start combat with an enemy
     * @param {string} enemyType - Type of enemy to fight
     * @returns {Promise<void>}
     */
    async function startCombat(enemyType) {
        const gameState = window.GameState;

        if (!gameState.sessionId) {
            window.showError('No active session. Start a new adventure first.');
            return;
        }

        try {
            const response = await fetch('/combat/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: gameState.sessionId,
                    enemy_type: enemyType
                })
            });

            if (!response.ok) {
                throw new Error(`Combat start failed: ${response.status}`);
            }

            const data = await response.json();
            window.addMessage(data.narrative, 'narrator');

            if (data.combat_state) {
                showCombatHUD(data.combat_state);
            }

        } catch (error) {
            console.error('Start combat error:', error);
            window.showError(`Failed to start combat: ${error.message}`);
        }
    }

    // Expose functions to window
    window.showCombatHUD = showCombatHUD;
    window.hideCombatHUD = hideCombatHUD;
    window.updateCombatHUD = updateCombatHUD;
    window.showDiceRoll = showDiceRoll;
    window.executeCombatAction = executeCombatAction;
    window.startCombat = startCombat;

})();
