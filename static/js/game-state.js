/**
 * Pocket Portals - Game State Management
 * Central state management for the game application
 */

(function() {
    'use strict';

    // ===== State Variables =====
    const GameState = {
        // Session state
        sessionId: null,
        currentChoices: [],
        isLoading: false,
        turnCount: 1,

        // Combat state
        combatState: null,
        isInCombat: false,

        // Streaming state
        streamingMessageEl: null,
        streamingTextEl: null,
        streamingContent: '',
        currentAgent: 'narrator',
        lastScrollTime: 0,

        // Constants
        SCROLL_THROTTLE_MS: 100
    };

    // ===== DOM Element References =====
    const DOMElements = {
        // Story elements
        storyBox: null,
        choicesSection: null,
        choicesDiv: null,
        actionInput: null,
        submitBtn: null,
        loadingDiv: null,
        errorDiv: null,
        sessionDisplay: null,
        newGameBtn: null,
        responseIndicator: null,

        // Bottom sheet elements
        bottomSheet: null,
        bottomSheetOverlay: null,
        bottomSheetHandle: null,
        bottomSheetContent: null,
        sheetChoices: null,
        sheetActionInput: null,
        sheetSubmitBtn: null,

        // Header elements
        gameHeader: null,
        turnCounter: null,
        questTitle: null,
        questSubtitle: null,
        progressFill: null,

        // Combat elements
        combatHud: null,
        turnOrderList: null,
        playerHpBar: null,
        playerHpText: null,
        enemyNameLabel: null,
        enemyHpBar: null,
        enemyHpText: null,
        diceDisplay: null,
        diceResultText: null
    };

    /**
     * Initialize DOM element references
     * Should be called after DOM is ready
     */
    function initDOMElements() {
        // Story elements
        DOMElements.storyBox = document.getElementById('story');
        DOMElements.choicesSection = document.getElementById('choices-section');
        DOMElements.choicesDiv = document.getElementById('choices');
        DOMElements.actionInput = document.getElementById('action-input');
        DOMElements.submitBtn = document.getElementById('submit-btn');
        DOMElements.loadingDiv = document.getElementById('loading');
        DOMElements.errorDiv = document.getElementById('error');
        DOMElements.sessionDisplay = document.getElementById('session-display');
        DOMElements.newGameBtn = document.getElementById('new-game-btn');
        DOMElements.responseIndicator = document.getElementById('response-indicator');

        // Bottom sheet elements
        DOMElements.bottomSheet = document.getElementById('bottom-sheet');
        DOMElements.bottomSheetOverlay = document.getElementById('bottom-sheet-overlay');
        DOMElements.bottomSheetHandle = document.getElementById('bottom-sheet-handle');
        DOMElements.bottomSheetContent = document.getElementById('bottom-sheet-content');
        DOMElements.sheetChoices = document.getElementById('sheet-choices');
        DOMElements.sheetActionInput = document.getElementById('sheet-action-input');
        DOMElements.sheetSubmitBtn = document.getElementById('sheet-submit-btn');

        // Header elements
        DOMElements.gameHeader = document.getElementById('game-header');
        DOMElements.turnCounter = document.getElementById('turn-counter');
        DOMElements.questTitle = document.getElementById('quest-title');
        DOMElements.questSubtitle = document.getElementById('quest-subtitle');
        DOMElements.progressFill = document.getElementById('progress-fill');

        // Combat elements
        DOMElements.combatHud = document.getElementById('combat-hud');
        DOMElements.turnOrderList = document.getElementById('turn-order-list');
        DOMElements.playerHpBar = document.getElementById('player-hp-bar');
        DOMElements.playerHpText = document.getElementById('player-hp-text');
        DOMElements.enemyNameLabel = document.getElementById('enemy-name-label');
        DOMElements.enemyHpBar = document.getElementById('enemy-hp-bar');
        DOMElements.enemyHpText = document.getElementById('enemy-hp-text');
        DOMElements.diceDisplay = document.getElementById('dice-display');
        DOMElements.diceResultText = document.getElementById('dice-result-text');
    }

    // ===== Agent Configuration =====
    const AgentConfig = {
        narrator: {
            label: 'Narrator',
            icon: 'ra-scroll-unfurled',
            avatar: 'ra-scroll-unfurled',
            typingSpeed: { base: 30, variance: 15 } // Slower, dramatic
        },
        keeper: {
            label: 'Keeper',
            icon: 'ra-dice',
            avatar: 'ra-dice',
            typingSpeed: { base: 15, variance: 5 } // Fast, mechanical
        },
        jester: {
            label: 'Jester',
            icon: 'ra-mask',
            avatar: 'ra-mask',
            typingSpeed: { base: 25, variance: 20 } // Erratic, playful
        },
        player: {
            label: 'You',
            icon: 'ra-player',
            avatar: 'ra-player',
            typingSpeed: { base: 10, variance: 5 }
        }
    };

    // ===== Loading Phrases =====
    const LoadingPhrases = [
        'Adventuring',
        'Rolling dice',
        'Consulting the fates',
        'Weaving the tale',
        'Charting the path',
        'Summoning words'
    ];

    /**
     * Get a random loading phrase
     * @returns {string} Random loading phrase
     */
    function getRandomLoadingPhrase() {
        return LoadingPhrases[Math.floor(Math.random() * LoadingPhrases.length)];
    }

    // ===== State Getters/Setters =====

    /**
     * Reset game state to initial values
     */
    function resetState() {
        GameState.sessionId = null;
        GameState.currentChoices = [];
        GameState.isLoading = false;
        GameState.turnCount = 1;
        GameState.combatState = null;
        GameState.isInCombat = false;
        GameState.streamingMessageEl = null;
        GameState.streamingTextEl = null;
        GameState.streamingContent = '';
        GameState.currentAgent = 'narrator';
    }

    // Expose to window for cross-file access
    window.GameState = GameState;
    window.DOMElements = DOMElements;
    window.AgentConfig = AgentConfig;
    window.initDOMElements = initDOMElements;
    window.getRandomLoadingPhrase = getRandomLoadingPhrase;
    window.resetGameState = resetState;

})();
