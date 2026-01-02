/**
 * Pocket Portals - UI Controllers
 * Bottom Sheet, Game Header, and Response Indicator controllers
 */

(function() {
    'use strict';

    // ===== Bottom Sheet Controller =====
    const BottomSheet = {
        isExpanded: false,
        startY: 0,
        currentY: 0,
        isDragging: false,

        /**
         * Initialize the bottom sheet with touch and click handlers
         */
        init: function() {
            const { bottomSheetHandle, bottomSheetOverlay } = window.DOMElements;

            if (!bottomSheetHandle || !bottomSheetOverlay) {
                console.warn('BottomSheet: Required DOM elements not found');
                return;
            }

            // Touch events for handle
            bottomSheetHandle.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: true });
            document.addEventListener('touchmove', this.onTouchMove.bind(this), { passive: false });
            document.addEventListener('touchend', this.onTouchEnd.bind(this));

            // Click overlay to collapse
            bottomSheetOverlay.addEventListener('click', () => this.collapse());

            // Tap handle to toggle
            bottomSheetHandle.addEventListener('click', () => this.toggle());
        },

        /**
         * Handle touch start event
         * @param {TouchEvent} e - Touch event
         */
        onTouchStart: function(e) {
            this.isDragging = true;
            this.startY = e.touches[0].clientY;
            window.DOMElements.bottomSheet.style.transition = 'none';
        },

        /**
         * Handle touch move event
         * @param {TouchEvent} e - Touch event
         */
        onTouchMove: function(e) {
            if (!this.isDragging) return;

            this.currentY = e.touches[0].clientY;
            const diff = this.startY - this.currentY;
            const bottomSheet = window.DOMElements.bottomSheet;

            if (this.isExpanded) {
                // Dragging down from expanded state
                if (diff < 0) {
                    const translateY = Math.min(Math.abs(diff), window.innerHeight * 0.7);
                    bottomSheet.style.transform = `translateY(${translateY}px)`;
                }
            } else {
                // Dragging up from peek state
                if (diff > 0) {
                    const currentPeek = 180;
                    const maxExpand = window.innerHeight * 0.7;
                    bottomSheet.style.transform = `translateY(calc(100% - ${Math.min(currentPeek + diff, maxExpand)}px))`;
                }
            }
        },

        /**
         * Handle touch end event
         */
        onTouchEnd: function() {
            if (!this.isDragging) return;
            this.isDragging = false;

            const bottomSheet = window.DOMElements.bottomSheet;
            bottomSheet.style.transition = '';

            const diff = this.startY - this.currentY;
            const threshold = 50;

            // Trigger haptic feedback when snapping
            if (typeof window.hapticFeedback === 'function') {
                window.hapticFeedback('snap');
            }

            if (this.isExpanded && diff < -threshold) {
                this.collapse();
            } else if (!this.isExpanded && diff > threshold) {
                this.expand();
            } else {
                // Snap back
                if (this.isExpanded) {
                    this.expand();
                } else {
                    this.collapse();
                }
            }
        },

        /**
         * Expand the bottom sheet to full height
         */
        expand: function() {
            const { bottomSheet, bottomSheetOverlay } = window.DOMElements;

            this.isExpanded = true;
            bottomSheet.classList.add('expanded');
            bottomSheet.classList.remove('hidden');
            bottomSheet.style.transform = '';
            bottomSheetOverlay.classList.add('visible');
        },

        /**
         * Collapse the bottom sheet to peek height
         */
        collapse: function() {
            const { bottomSheet, bottomSheetOverlay } = window.DOMElements;

            this.isExpanded = false;
            bottomSheet.classList.remove('expanded');
            bottomSheet.classList.remove('hidden');
            bottomSheet.style.transform = '';
            bottomSheetOverlay.classList.remove('visible');
        },

        /**
         * Toggle between expanded and collapsed states
         */
        toggle: function() {
            if (this.isExpanded) {
                this.collapse();
            } else {
                this.expand();
            }
        },

        /**
         * Hide the bottom sheet completely
         */
        hide: function() {
            const { bottomSheet, bottomSheetOverlay } = window.DOMElements;

            bottomSheet.classList.add('hidden');
            bottomSheet.classList.remove('expanded');
            bottomSheetOverlay.classList.remove('visible');
            this.isExpanded = false;
        },

        /**
         * Show the bottom sheet in peek state
         */
        show: function() {
            window.DOMElements.bottomSheet.classList.remove('hidden');
        },

        /**
         * Update the choices displayed in the bottom sheet
         * @param {Array<string>} choices - Array of choice strings
         */
        updateChoices: function(choices) {
            const { sheetChoices } = window.DOMElements;
            if (!sheetChoices) return;

            sheetChoices.innerHTML = '';
            const icons = ['ra-axe', 'ra-speech-bubble', 'ra-boot-stomp'];

            choices.forEach((choice, i) => {
                const btn = document.createElement('button');
                btn.className = 'sheet-choice-btn';
                btn.innerHTML = `
                    <i class="ra ${icons[i] || 'ra-hand'}"></i>
                    <span class="sheet-choice-text">${choice}</span>
                `;
                btn.onclick = () => {
                    // Trigger haptic feedback for choice selection
                    if (typeof window.hapticFeedback === 'function') {
                        window.hapticFeedback('light');
                    }
                    this.collapse();
                    if (typeof window.selectChoice === 'function') {
                        window.selectChoice(i + 1);
                    }
                };
                sheetChoices.appendChild(btn);
            });

            if (choices.length > 0) {
                this.show();
            } else {
                this.hide();
            }
        }
    };

    // ===== Game Header Controller =====
    const GameHeader = {
        lastScrollY: 0,
        milestones: ['start', 'explore', 'challenge', 'climax', 'resolution'],
        currentMilestone: 0,

        /**
         * Initialize the game header with scroll handlers
         */
        init: function() {
            window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
        },

        /**
         * Handle scroll events for header effects
         */
        onScroll: function() {
            const currentScrollY = window.scrollY;
            const { gameHeader } = window.DOMElements;

            if (!gameHeader) return;

            // Add shadow when scrolled
            if (currentScrollY > 10) {
                gameHeader.classList.add('scrolled');
            } else {
                gameHeader.classList.remove('scrolled');
            }

            this.lastScrollY = currentScrollY;
        },

        /**
         * Update the turn counter display
         * @param {number} count - Current turn number
         */
        updateTurn: function(count) {
            const { turnCounter, progressFill } = window.DOMElements;

            window.GameState.turnCount = count;

            if (turnCounter) {
                turnCounter.textContent = count;
            }

            // Update progress based on turn count
            if (progressFill) {
                const progress = Math.min((count / 20) * 100, 100);
                progressFill.style.width = `${progress}%`;
            }

            // Update milestones
            const milestoneIndex = Math.floor(count / 5);
            this.setMilestone(Math.min(milestoneIndex, this.milestones.length - 1));
        },

        /**
         * Set the current milestone in the progress bar
         * @param {number} index - Milestone index (0-4)
         */
        setMilestone: function(index) {
            this.currentMilestone = index;
            const milestoneEls = document.querySelectorAll('.milestone');

            milestoneEls.forEach((el, i) => {
                el.classList.remove('reached', 'current');
                if (i < index) {
                    el.classList.add('reached');
                } else if (i === index) {
                    el.classList.add('current');
                }
            });
        },

        /**
         * Set the quest title and optional subtitle
         * @param {string} title - Quest title
         * @param {string|null} subtitle - Optional subtitle
         */
        setQuestTitle: function(title, subtitle) {
            const { questTitle, questSubtitle } = window.DOMElements;

            if (questTitle) {
                questTitle.textContent = title || 'Pocket Portals';
            }

            if (subtitle && questSubtitle) {
                questSubtitle.textContent = subtitle;
            }
        }
    };

    // ===== Response Indicator Controller =====
    const ResponseIndicator = {
        /**
         * Show the response indicator for a specific agent
         * @param {string} agentType - Agent type (narrator, keeper, jester, player)
         */
        show: function(agentType) {
            const { responseIndicator } = window.DOMElements;
            const config = window.AgentConfig[agentType] || window.AgentConfig.narrator;

            if (!responseIndicator) return;

            responseIndicator.className = `response-indicator visible agent-${agentType}`;

            const avatarEl = responseIndicator.querySelector('.agent-avatar');
            if (avatarEl) {
                avatarEl.innerHTML = `<i class="ra ${config.icon}"></i>`;
            }

            const nameEl = responseIndicator.querySelector('.agent-name');
            if (nameEl) {
                nameEl.textContent = config.label;
            }
        },

        /**
         * Hide the response indicator
         */
        hide: function() {
            const { responseIndicator } = window.DOMElements;
            if (responseIndicator) {
                responseIndicator.classList.remove('visible');
            }
        }
    };

    // Expose controllers to window
    window.BottomSheet = BottomSheet;
    window.GameHeader = GameHeader;
    window.ResponseIndicator = ResponseIndicator;

})();
